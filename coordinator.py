"""Coordination des appels à l’API PRIM pour IDF Mobilité Assistant.

Un seul `DataUpdateCoordinator` par entrée de configuration interroge l’API
pour l’ensemble des capteurs (lignes + messages).

Cela remplace les minuteurs individuels posés par capteur, qui déclenchaient
un appel toutes les 60 secondes, soit 1 440 appels par jour et par capteur —
au-delà du quota PRIM (1 000 requêtes/jour pour les comptes récents).

Les appels sont en plus dédupliqués : deux capteurs pointant sur le même
arrêt (ou la même ligne) ne déclenchent qu’une seule requête par cycle.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_API_KEY,
    CONF_NIGHT_PAUSE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    NIGHT_PAUSE_END,
    NIGHT_PAUSE_START,
    PRIM_LINE_REPORTS_URL,
    PRIM_STOP_MONITORING_URL,
    REQUEST_TIMEOUT,
)
from .utils import as_record_list

_LOGGER = logging.getLogger(__name__)

STATUS_OK = "OK"
STATUS_API_KEY_ERROR = "API_KEY_ERROR"

# Type des données exposées aux capteurs :
# {"lignes": {uuid: (status, payload)}, "messages": {uuid: (status, payload)}}
PRIMData = dict[str, dict[str, tuple[str, dict[str, Any]]]]


def _scan_interval_seconds(options: Mapping[str, Any]) -> int:
    """Retourner l’intervalle de rafraîchissement configuré, borné."""
    try:
        interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    except (TypeError, ValueError):
        interval = DEFAULT_SCAN_INTERVAL

    return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, interval))


def _in_night_pause(now: datetime) -> bool:
    """Indiquer si l’heure locale tombe dans la fenêtre de pause nocturne."""
    return NIGHT_PAUSE_START <= now.time() < NIGHT_PAUSE_END


async def _fetch_json(
    session: aiohttp.ClientSession,
    api_key: str,
    url: str,
    params: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Appeler l’API PRIM et normaliser le résultat.

    Retourne un tuple ``(status, payload)`` où ``status`` décrit la réponse.
    Aucune exception n’est levée : l’état du capteur porte l’information.
    """
    try:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            async with session.get(
                url, headers={"apiKey": api_key}, params=params
            ) as resp:
                if resp.status == 200:
                    return STATUS_OK, await resp.json()

                if resp.status in (401, 403):
                    return STATUS_API_KEY_ERROR, {"http_status": resp.status}

                if resp.status == 429:
                    return "RATE_LIMIT", {"http_status": resp.status}

                if resp.status >= 500:
                    return "SERVER_ERROR", {"http_status": resp.status}

                return "HTTP_ERROR", {"http_status": resp.status}

    except TimeoutError:
        return "TIMEOUT", {"error": f"délai dépassé ({REQUEST_TIMEOUT} s)"}

    except aiohttp.ClientError as err:
        return "CLIENT_ERROR", {"error": str(err)}

    except ValueError as err:
        return "INVALID_JSON", {"error": str(err)}


class PRIMCoordinator(DataUpdateCoordinator[PRIMData]):
    """Récupère les données PRIM de tous les capteurs d’une entrée."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialiser le coordinateur à partir des données de l’entrée."""
        options = entry.options

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=_scan_interval_seconds(options)),
        )

        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._night_pause = bool(options.get(CONF_NIGHT_PAUSE, False))

        self.lignes: list[dict[str, Any]] = as_record_list(
            entry.data.get("lignes", [])
        )
        self.messages: list[dict[str, Any]] = as_record_list(
            entry.data.get("messages", [])
        )

    @property
    def api_key(self) -> str | None:
        """Retourner la clé API courante (relue à chaque cycle)."""
        return self._entry.data.get(CONF_API_KEY)

    async def _async_update_data(self) -> PRIMData:
        """Interroger l’API PRIM pour tous les capteurs de l’entrée."""
        api_key = self.api_key

        if not api_key:
            raise ConfigEntryAuthFailed("Aucune clé API PRIM n’est configurée")

        if self._night_pause and _in_night_pause(dt_util.now()):
            # Réseau interrompu : aucun appel, on conserve le dernier état connu.
            # (Ne jamais retourner None ici, sinon les capteurs perdent leur état.)
            return self.data or {"lignes": {}, "messages": {}}

        # Déduplication : une requête par arrêt / par ligne unique
        jobs: dict[tuple[str, str], Any] = {}

        for monitoring_ref in sorted({ligne["monitoring_ref"] for ligne in self.lignes}):
            jobs[("ligne", monitoring_ref)] = _fetch_json(
                self._session,
                api_key,
                PRIM_STOP_MONITORING_URL,
                {"MonitoringRef": monitoring_ref},
            )

        for line_id in sorted({message["line_id"] for message in self.messages}):
            jobs[("message", line_id)] = _fetch_json(
                self._session,
                api_key,
                PRIM_LINE_REPORTS_URL.format(line_id=line_id),
                {"filter_status[]": "active", "disable_geojson": "true"},
            )

        if not jobs:
            return {"lignes": {}, "messages": {}}

        results = await asyncio.gather(*jobs.values(), return_exceptions=True)

        payloads: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
        for key, result in zip(jobs, results, strict=True):
            if isinstance(result, BaseException):
                payloads[key] = ("ERROR", {"error": str(result)})
            else:
                payloads[key] = result

        # Clé API refusée → déclenche le flux de réauthentification
        if any(status == STATUS_API_KEY_ERROR for status, _ in payloads.values()):
            raise ConfigEntryAuthFailed("La clé API PRIM a été refusée")

        # Tous les appels ont échoué → l’entrée passe en échec de mise à jour
        if all(status != STATUS_OK for status, _ in payloads.values()):
            status, raw = next(iter(payloads.values()))
            raise UpdateFailed(
                f"Tous les appels PRIM ont échoué (statut : {status}, détail : {raw})"
            )

        data: PRIMData = {"lignes": {}, "messages": {}}

        for ligne in self.lignes:
            data["lignes"][ligne["uuid"]] = payloads[("ligne", ligne["monitoring_ref"])]

        for message in self.messages:
            data["messages"][message["uuid"]] = payloads[("message", message["line_id"])]

        return data
