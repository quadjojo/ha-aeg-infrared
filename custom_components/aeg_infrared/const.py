"""Constants for the AEG Infrared integration."""
from __future__ import annotations

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACMode,
    SWING_OFF,
    SWING_ON,
)

DOMAIN = "aeg_infrared"

CONF_INFRARED_ENTITY_ID = "infrared_entity_id"
CONF_MODEL = "model"

# Models believed to share the Electra IR protocol used by AEG's Chillflex
# Pro line. Only AXP26U338CW is explicitly registered in pyhvac's aeg.py
# plugin; the rest are sister models in the same family that we route to
# the same encoder. Heat-pump variants (suffix "HW") accept the same
# encoder for cool/dry/fan/auto and additionally honour `heat`.
MODEL_AXP26U338CW = "Chillflex Pro AXP26U338CW"
MODEL_AXP34U338CW = "Chillflex Pro AXP34U338CW"
MODEL_AXP26U558HW = "Chillflex Pro AXP26U558HW"

SUPPORTED_MODELS: tuple[str, ...] = (
    MODEL_AXP34U338CW,
    MODEL_AXP26U338CW,
    MODEL_AXP26U558HW,
)

# In pyhvac the AEG plugin only registers AXP26U338CW. Other models are
# routed to the same Electra encoder.
PYHVAC_MODEL_FALLBACKS: dict[str, str] = {
    MODEL_AXP34U338CW: MODEL_AXP26U338CW,
    MODEL_AXP26U558HW: MODEL_AXP26U338CW,
}

MIN_TEMP = 16
MAX_TEMP = 32
DEFAULT_TARGET_TEMP = 22
PRECISION = 1.0

HVAC_MODES: list[HVACMode] = [
    HVACMode.OFF,
    HVACMode.AUTO,
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.HEAT,
]

FAN_MODES: list[str] = [FAN_AUTO, FAN_HIGH, FAN_MEDIUM, FAN_LOW]
# Modes in which the AC accepts a user-selected fan speed. In any other
# HVAC mode the fan is forced to auto and the UI is restricted to it.
FAN_VARIABLE_MODES: tuple[HVACMode, ...] = (
    HVACMode.COOL,
    HVACMode.HEAT,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
)
SWING_MODES: list[str] = [SWING_OFF, SWING_ON]

# Translation HA HVAC mode → pyhvac mode string.
HVAC_TO_PYHVAC: dict[HVACMode, str] = {
    HVACMode.OFF: "off",
    HVACMode.AUTO: "auto",
    HVACMode.COOL: "cool",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "fan",
    HVACMode.HEAT: "heat",
}

FAN_TO_PYHVAC: dict[str, str] = {
    FAN_AUTO: "auto",
    FAN_HIGH: "high",
    FAN_MEDIUM: "medium",
    FAN_LOW: "low",
}

# pyhvac's Electra plugin advertises ["off", "on"] as the swing capability,
# but the underlying IRGHVAC.trans_swing() only knows the keys
# {"off", "auto", "auto high", "auto low", "ceiling", "90°", ...}. Sending
# "on" silently drops the swing bit, so we map straight to "auto".
SWING_TO_PYHVAC: dict[str, str] = {
    SWING_OFF: "off",
    SWING_ON: "auto",
}
