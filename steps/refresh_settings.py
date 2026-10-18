"""Étape de réglage du rafraîchissement dans le flux de configuration.

Cette étape permet de modifier l’intervalle de rafraîchissement des capteurs
et d’activer la pause nocturne, qui évite de consommer du quota PRIM pendant
l’interruption de trafic (01:30 → 05:30).
"""

import voluptuous as vol

from ..const import (  # noqa: TID252
    CONF_NIGHT_PAUSE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class StepRefreshSettings:
    """Étape du flux permettant de régler le rafraîchissement."""

    async def async_step_refresh_settings(self, user_input=None):
        """Afficher le formulaire de réglage et traiter la validation.

        - Si `user_input` est fourni : les options sont enregistrées dans la
          config_entry, puis l’intégration est rechargée pour appliquer le
          nouvel intervalle au coordinateur.
        - Sinon : affichage du formulaire avec les valeurs actuelles.
        """
        options = self.entry.options

        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.entry,
                options={**options, **user_input},
            )

            await self.hass.config_entries.async_reload(self.entry.entry_id)

            return await self.async_step_main_menu()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Required(
                    CONF_NIGHT_PAUSE,
                    default=options.get(CONF_NIGHT_PAUSE, False),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="refresh_settings",
            data_schema=schema,
            errors={},
            description_placeholders={
                "min_interval": str(MIN_SCAN_INTERVAL),
                "max_interval": str(MAX_SCAN_INTERVAL),
            },
        )
