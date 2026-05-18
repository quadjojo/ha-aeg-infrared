"""Common entity for AEG Infrared integration."""
from __future__ import annotations

import logging

from homeassistant.components.infrared import async_send_command
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .commands import AegAcCommand, AegAcState
from .const import CONF_MODEL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AegIrEntity(Entity):
    """Base entity for AEG IR devices, bound to an infrared emitter."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_entity_id: str,
        unique_id_suffix: str,
    ) -> None:
        self._infrared_entity_id = infrared_entity_id
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        model = entry.data.get(CONF_MODEL, "AEG AC")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"AEG {model}",
            manufacturer="AEG",
            model=model,
        )

    async def async_added_to_hass(self) -> None:
        """Track availability of the bound infrared emitter."""
        await super().async_added_to_hass()

        @callback
        def _ir_state_changed(event: Event[EventStateChangedData]) -> None:
            new_state = event.data["new_state"]
            ir_available = (
                new_state is not None and new_state.state != STATE_UNAVAILABLE
            )
            if ir_available != self.available:
                _LOGGER.info(
                    "Infrared emitter %s used by %s is %s",
                    self._infrared_entity_id,
                    self.entity_id,
                    "available" if ir_available else "unavailable",
                )
                self._attr_available = ir_available
                self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._infrared_entity_id], _ir_state_changed
            )
        )

        ir_state = self.hass.states.get(self._infrared_entity_id)
        self._attr_available = (
            ir_state is not None and ir_state.state != STATE_UNAVAILABLE
        )

    async def _send_state(self, state: AegAcState) -> None:
        """Build and send an AC command via the infrared building block."""
        command = AegAcCommand(state=state)
        await async_send_command(
            self.hass,
            self._infrared_entity_id,
            command,
            context=self._context,
        )
