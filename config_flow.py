"""Flux de configuration pour l’intégration IDF Mobilité Assistant.

Ce module gère la génération dynamique des méthodes `async_step_*`
à partir des mixins de steps, ainsi que la classe principale `ConfigFlow`.
"""

from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

from .const import CONF_API_KEY, DOMAIN
from .steps.delete import StepDelete
from .steps.main_menu import StepMainMenu
from .steps.refresh_settings import StepRefreshSettings
from .steps.search_line import SearchLineStep
from .steps.search_stop_area import SearchStopAreaStep
from .steps.select_line import SelectLineStep
from .steps.select_stop_area import StepSelectStopArea
from .steps.update_api import StepUpdateApi
from .steps.user import StepUser


def inject_step_methods(target_cls, *mixins) -> None:
    """Injecter automatiquement les méthodes async_step_* dans la classe cible.

    Cette fonction parcourt les mixins fournis et copie toutes les méthodes
    commençant par `async_step_` dans la classe `target_cls`. Cela permet
    de composer dynamiquement le flux de configuration sans héritage multiple.
    """
    for mixin in mixins:
        for name, method in mixin.__dict__.items():
            if name.startswith("async_step_") and callable(method):

                async def wrapper(self, user_input=None, _method=method):
                    """Appeler la méthode du mixin correspondant."""
                    return await _method(self, user_input)

                setattr(target_cls, name, wrapper)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration principal pour l’intégration IDF Mobilité Assistant."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialiser le flux de configuration.

        Initialise les variables internes utilisées par les différents steps.
        """
        self.entry = None
        self.api_key = None
        self._search_results = {}
        self._selected_stop_area = None
        self._first_line_name = None
        self._first_line = False

    # ---------------------------------------------------------
    # Réauthentification (clé API refusée par PRIM)
    # ---------------------------------------------------------

    async def async_step_reauth(self, entry_data: dict):
        """Démarrer le flux de réauthentification sur refus de la clé API."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Demander une nouvelle clé API puis recharger l’entrée.

        Ce flux est déclenché automatiquement par Home Assistant lorsqu’un
        coordinateur lève `ConfigEntryAuthFailed` (HTTP 401 / 403).
        """
        errors = {}

        if user_input is not None:
            key = user_input[CONF_API_KEY].strip()

            if not key:
                errors["base"] = "api_key_empty"
            else:
                return self.async_update_reload_and_abort(
                    self.entry,
                    data={**self.entry.data, CONF_API_KEY: key},
                    reason="reauth_successful",
                )

        schema = vol.Schema({vol.Required(CONF_API_KEY): str})

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={},
        )

    # ---------------------------------------------------------
    # Flux d’options (« Configurer »)
    # ---------------------------------------------------------

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Retourner le flux d’options associé au bouton « Configurer »."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Flux d’options de l’intégration (bouton « Configurer »).

    Il expose les mêmes étapes que le flux de configuration (mêmes mixins),
    ce qui évite toute divergence entre les deux chemins d’accès : ajout d’une
    ligne, ajout d’un message, suppression, rotation de la clé API et réglage
    du rafraîchissement.
    """

    async def async_step_init(self, user_input=None):
        """Point d’entrée du flux d’options : menu principal."""
        return await self.async_step_main_menu(user_input)

    @property
    def entry(self) -> config_entries.ConfigEntry:
        """Exposer l’entrée attendue par les étapes partagées.

        `config_entry` n’est disponible qu’après l’initialisation du flux,
        d’où cette propriété évaluée à l’accès.
        """
        return self.config_entry


# ---------------------------------------------------------
# Injection des steps dans ConfigFlow
# ---------------------------------------------------------

inject_step_methods(
    ConfigFlow,
    StepUser,
    SearchStopAreaStep,
    StepSelectStopArea,
    StepMainMenu,
    SearchLineStep,
    SelectLineStep,
    StepDelete,
    StepUpdateApi,
    StepRefreshSettings,
)

# Le flux d’options ne propose pas la saisie initiale de la clé API
# (elle existe déjà) ni la réauthentification (gérée par Home Assistant).
inject_step_methods(
    OptionsFlowHandler,
    StepMainMenu,
    SearchStopAreaStep,
    StepSelectStopArea,
    SearchLineStep,
    SelectLineStep,
    StepDelete,
    StepUpdateApi,
    StepRefreshSettings,
)
