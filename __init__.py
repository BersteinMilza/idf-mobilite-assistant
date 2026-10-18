"""Logique d’initialisation de l’intégration IDF Mobilité Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PRIMCoordinator

import homeassistant.helpers.config_validation as cv

CONFIG_SCHEMA = cv.config_entry_only_config_schema("idf_mobilite_assistant")

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Configurer l’intégration via YAML.

    Cette intégration ne supporte pas la configuration YAML, mais cette
    fonction est requise par Home Assistant. Elle initialise simplement
    l’espace de stockage du domaine.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurer l’intégration lors de l’ajout d’une entrée de configuration.

    Crée le coordinateur, effectue un premier rafraîchissement (qui échoue
    proprement via `ConfigEntryNotReady` ou démarre la réauthentification
    via `ConfigEntryAuthFailed`), puis délègue la création des entités à la
    plateforme `sensor`.
    """
    hass.data.setdefault(DOMAIN, {})

    coordinator = PRIMCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger l’intégration lors de la suppression de l’entrée de configuration."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unloaded
