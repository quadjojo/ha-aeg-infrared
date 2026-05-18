"""Config flow for AEG Infrared."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_INFRARED_ENTITY_ID,
    CONF_MODEL,
    DOMAIN,
    MODEL_AXP34U338CW,
    SUPPORTED_MODELS,
)


class AegIrConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for AEG Infrared."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        emitter_entity_ids = async_get_emitters(self.hass)
        if not emitter_entity_ids:
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            entity_id = user_input[CONF_INFRARED_ENTITY_ID]
            model = user_input[CONF_MODEL]

            await self.async_set_unique_id(f"aeg_{model}_{entity_id}")
            self._abort_if_unique_id_configured()

            ent_reg = er.async_get(self.hass)
            entry = ent_reg.async_get(entity_id)
            emitter_name = (
                entry.name or entry.original_name or entity_id
                if entry
                else entity_id
            )
            return self.async_create_entry(
                title=f"AEG {model} via {emitter_name}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL, default=MODEL_AXP34U338CW
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=list(SUPPORTED_MODELS),
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_INFRARED_ENTITY_ID): EntitySelector(
                        EntitySelectorConfig(
                            domain=INFRARED_DOMAIN,
                            include_entities=emitter_entity_ids,
                        )
                    ),
                }
            ),
        )
