"""Plateformes de capteurs PRIM pour l’intégration IDF Mobilité Assistant.

Ce module gère :
- la création des entités (lignes + messages),
- la base factorisée des capteurs PRIM,
- les capteurs spécialisés StopMonitoring et Messages.

Les capteurs ne font aucun appel réseau : ils lisent les données préparées
par `PRIMCoordinator`. Le contenu des attributs est consommé tel quel par la
carte Lovelace `lovelace-idf-mobilite`, qui attend :
- `Siri` (payload SIRI brut) pour les capteurs de lignes,
- `disruptions` + `line_reports` (payload Navitia brut) pour les messages.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PRIMCoordinator, STATUS_OK

_ICON_BY_TYPE = {
    "bus": "mdi:bus",
    "metro": "mdi:subway",
    "tram": "mdi:tram",
    "rail": "mdi:train",
    "cableway": "mdi:cable-car",
}


# ============================================================
#  SETUP ENTRY
# ============================================================


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créer toutes les entités (Lignes + Messages) d’une entrée de configuration."""
    coordinator: PRIMCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        PRIMLigneSensor(coordinator, ligne) for ligne in coordinator.lignes
    ]
    entities += [
        PRIMMessageSensor(coordinator, message) for message in coordinator.messages
    ]

    async_add_entities(entities)


# ============================================================
#  BASE SENSOR FACTORISÉ
# ============================================================


class PRIMBaseSensor(CoordinatorEntity[PRIMCoordinator], SensorEntity):
    """Classe de base commune pour les capteurs PRIM.

    Fournit la lecture des données du coordinateur, l’état
    (statut de l’appel API) et la disponibilité de l’entité.
    """

    _kind: str

    def __init__(self, coordinator: PRIMCoordinator, uuid: str) -> None:
        """Initialiser le capteur de base."""
        super().__init__(coordinator)
        self._uuid = uuid

    # --------------------------------------------------
    #  Accès aux données
    # --------------------------------------------------

    @property
    def _payload(self) -> tuple[str | None, dict[str, Any]]:
        """Retourner le couple (statut, payload brut) de ce capteur."""
        data = self.coordinator.data or {}
        return data.get(self._kind, {}).get(self._uuid, (None, {}))

    @property
    def native_value(self) -> str | None:
        """Retourner le statut du dernier appel API (OK, RATE_LIMIT, …)."""
        return self._payload[0]

    @property
    def available(self) -> bool:
        """Indiquer si le capteur a des données exploitables."""
        return super().available and self._payload[0] is not None


# ============================================================
#  SENSOR : LIGNES
# ============================================================


class PRIMLigneSensor(PRIMBaseSensor):
    """Capteur PRIM StopMonitoring (Lignes)."""

    _kind = "lignes"

    def __init__(self, coordinator: PRIMCoordinator, ligne: dict[str, Any]) -> None:
        """Initialiser un capteur de ligne PRIM."""
        super().__init__(coordinator, ligne["uuid"])

        self._stop_name = ligne["stop_name"]
        self._town = ligne["town"]
        self._arr_type = ligne["arr_type"]
        self._monitoring_ref = ligne["monitoring_ref"]

        name = ligne.get("name")
        if name:
            self._attr_name = name
        else:
            suffix = " – Multimodal" if self._arr_type == "multimodal" else ""
            self._attr_name = f"{self._stop_name} ({self._town}){suffix}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, "lignes")},
            "name": "Lignes",
            "manufacturer": "PRIM",
        }

    @property
    def unique_id(self) -> str:
        """Retourner l’identifiant unique du capteur."""
        return f"{DOMAIN}_ligne_{self._uuid}"

    @property
    def icon(self) -> str:
        """Retourner l’icône correspondant au type de ligne."""
        return _ICON_BY_TYPE.get(self._arr_type, "mdi:train-bus")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Retourner les attributs du capteur de ligne."""
        status, raw = self._payload

        base = {
            "name": self._stop_name,
            "town": self._town,
            "monitoring_ref": self._monitoring_ref,
            "type": self._arr_type,
        }

        if status == STATUS_OK:
            return {**base, "Siri": raw.get("Siri", {}), "http_status": 200}

        return {**base, **raw}


# ============================================================
#  SENSOR : MESSAGES
# ============================================================


class PRIMMessageSensor(PRIMBaseSensor):
    """Capteur PRIM Messages (Navitia line_reports)."""

    _kind = "messages"

    def __init__(self, coordinator: PRIMCoordinator, message: dict[str, Any]) -> None:
        """Initialiser un capteur de messages PRIM."""
        super().__init__(coordinator, message["uuid"])

        self._line_id = message["line_id"]
        self._line_type = message["line_type"]
        self._attr_name = message["name"]
        self._attr_icon = "mdi:message-bulleted"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "messages")},
            "name": "Messages",
            "manufacturer": "PRIM",
        }

    @property
    def unique_id(self) -> str:
        """Retourner l’identifiant unique du capteur."""
        return f"{DOMAIN}_messages_{self._uuid}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Retourner les attributs du capteur de messages."""
        status, raw = self._payload

        if status == STATUS_OK:
            return {
                "line_id": self._line_id,
                "line_type": self._line_type,
                "disruptions": raw.get("disruptions", []),
                "line_reports": raw.get("line_reports", []),
                "http_status": 200,
            }

        return raw
