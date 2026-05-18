"""Climate platform for AEG Infrared."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_SWING_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from homeassistant.components.climate import FAN_AUTO

from .commands import AegAcState
from .const import (
    CONF_INFRARED_ENTITY_ID,
    DEFAULT_TARGET_TEMP,
    FAN_MODES,
    FAN_TO_PYHVAC,
    FAN_VARIABLE_MODES,
    HVAC_MODES,
    HVAC_TO_PYHVAC,
    MAX_TEMP,
    MIN_TEMP,
    PRECISION,
    SWING_MODES,
    SWING_TO_PYHVAC,
)
from .entity import AegIrEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AEG IR climate from a config entry."""
    infrared_entity_id = entry.data[CONF_INFRARED_ENTITY_ID]
    async_add_entities([AegIrClimate(entry, infrared_entity_id)])


class AegIrClimate(AegIrEntity, ClimateEntity, RestoreEntity):
    """AEG portable AC controlled via the infrared building block."""

    _attr_name = None
    _attr_assumed_state = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = PRECISION
    _attr_precision = PRECISION
    _attr_hvac_modes = HVAC_MODES
    _attr_swing_modes = SWING_MODES
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, entry: ConfigEntry, infrared_entity_id: str) -> None:
        super().__init__(entry, infrared_entity_id, unique_id_suffix="climate")
        self._attr_hvac_mode = HVACMode.OFF
        self._last_active_mode: HVACMode = HVACMode.COOL
        self._attr_target_temperature: float = float(DEFAULT_TARGET_TEMP)
        self._attr_fan_mode = FAN_AUTO
        self._attr_swing_mode = SWING_MODES[0]

    @property
    def fan_modes(self) -> list[str]:
        """Restrict the fan dropdown to `auto` while in off/auto HVAC modes.

        In `off` and `auto` the AC chooses the fan speed itself, so the
        physical remote also locks the fan to auto. We mirror that — the
        UI hides the other options to prevent users from selecting a
        speed that the AC will silently ignore.
        """
        if self._attr_hvac_mode in FAN_VARIABLE_MODES:
            return list(FAN_MODES)
        return [FAN_AUTO]

    async def async_added_to_hass(self) -> None:
        """Restore last known desired state without re-transmitting."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            mode = HVACMode(last_state.state)
        except ValueError:
            mode = HVACMode.OFF
        self._attr_hvac_mode = mode
        if mode != HVACMode.OFF:
            self._last_active_mode = mode

        attrs = last_state.attributes
        if (temp := attrs.get(ATTR_TEMPERATURE)) is not None:
            try:
                self._attr_target_temperature = float(temp)
            except (TypeError, ValueError):
                pass
        if (fan := attrs.get(ATTR_FAN_MODE)) in FAN_MODES:
            self._attr_fan_mode = fan
        if (swing := attrs.get(ATTR_SWING_MODE)) in SWING_MODES:
            self._attr_swing_mode = swing
        # Enforce the auto/off fan-lock invariant after restore so the
        # UI never opens with a forbidden combination.
        if self._attr_hvac_mode not in FAN_VARIABLE_MODES:
            self._attr_fan_mode = FAN_AUTO

    @property
    def hvac_action(self) -> HVACAction | None:
        """Best-effort hvac_action — IR is one-way."""
        match self._attr_hvac_mode:
            case HVACMode.OFF:
                return HVACAction.OFF
            case HVACMode.COOL:
                return HVACAction.COOLING
            case HVACMode.HEAT:
                return HVACAction.HEATING
            case HVACMode.DRY:
                return HVACAction.DRYING
            case HVACMode.FAN_ONLY:
                return HVACAction.FAN
            case HVACMode.AUTO:
                return HVACAction.IDLE
        return None

    def _current_state(self) -> AegAcState:
        temp = int(round(self._attr_target_temperature or DEFAULT_TARGET_TEMP))
        temp = max(MIN_TEMP, min(MAX_TEMP, temp))
        return AegAcState(
            mode=HVAC_TO_PYHVAC[self._attr_hvac_mode],
            temperature=temp,
            fan=FAN_TO_PYHVAC[self._attr_fan_mode],
            swing=SWING_TO_PYHVAC[self._attr_swing_mode],
        )

    async def _transmit(self) -> None:
        try:
            await self._send_state(self._current_state())
        except HomeAssistantError:
            raise
        except Exception as err:  # pyhvac/encoding failure → surface clearly
            raise HomeAssistantError(
                f"Failed to send AEG IR command: {err}"
            ) from err

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode not in HVAC_MODES:
            raise HomeAssistantError(f"Unsupported HVAC mode: {hvac_mode}")
        if hvac_mode == self._attr_hvac_mode:
            return
        self._attr_hvac_mode = hvac_mode
        if hvac_mode != HVACMode.OFF:
            self._last_active_mode = hvac_mode
        # Auto and off lock the fan to auto on the physical remote, so
        # we mirror that here — otherwise the IR frame would carry a
        # fan-speed bit the AC ignores anyway.
        if hvac_mode not in FAN_VARIABLE_MODES:
            self._attr_fan_mode = FAN_AUTO
        await self._transmit()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        target = kwargs.get(ATTR_TEMPERATURE)
        if target is None:
            return
        new_temp = float(target)
        if new_temp < MIN_TEMP or new_temp > MAX_TEMP:
            raise HomeAssistantError(
                f"Target temperature {new_temp} outside [{MIN_TEMP},{MAX_TEMP}]"
            )

        new_mode = kwargs.get(ATTR_HVAC_MODE)
        changed = False
        if new_temp != self._attr_target_temperature:
            self._attr_target_temperature = new_temp
            changed = True
        if new_mode is not None and new_mode != self._attr_hvac_mode:
            if new_mode not in HVAC_MODES:
                raise HomeAssistantError(f"Unsupported HVAC mode: {new_mode}")
            self._attr_hvac_mode = new_mode
            if new_mode != HVACMode.OFF:
                self._last_active_mode = new_mode
            changed = True
        elif self._attr_hvac_mode == HVACMode.OFF:
            # Setting a temperature while OFF implies powering on into cool.
            self._attr_hvac_mode = HVACMode.COOL
            self._last_active_mode = HVACMode.COOL
            changed = True

        if not changed:
            return
        await self._transmit()
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in FAN_MODES:
            raise HomeAssistantError(f"Unsupported fan mode: {fan_mode}")
        if self._attr_hvac_mode not in FAN_VARIABLE_MODES:
            # In off/auto the fan is locked to auto. Reject any other
            # selection — the UI already hides them, but defend against
            # direct service calls.
            if fan_mode != FAN_AUTO:
                raise HomeAssistantError(
                    f"Fan mode is locked to '{FAN_AUTO}' while HVAC mode is "
                    f"'{self._attr_hvac_mode}'. Switch to cool/heat/dry/"
                    "fan_only first."
                )
            return
        if fan_mode == self._attr_fan_mode:
            return
        self._attr_fan_mode = fan_mode
        await self._transmit()
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        if swing_mode not in SWING_MODES:
            raise HomeAssistantError(f"Unsupported swing mode: {swing_mode}")
        if swing_mode == self._attr_swing_mode:
            return
        self._attr_swing_mode = swing_mode
        if self._attr_hvac_mode == HVACMode.OFF:
            self.async_write_ha_state()
            return
        await self._transmit()
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        if self._attr_hvac_mode != HVACMode.OFF:
            return
        self._attr_hvac_mode = self._last_active_mode or HVACMode.COOL
        await self._transmit()
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        if self._attr_hvac_mode == HVACMode.OFF:
            return
        self._attr_hvac_mode = HVACMode.OFF
        await self._transmit()
        self.async_write_ha_state()
