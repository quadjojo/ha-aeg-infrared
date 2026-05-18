"""IR command construction for AEG portable air conditioners.

Wraps the pyhvac Electra encoder into an infrared_protocols.Command so it
plugs into Home Assistant's native infrared building block.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from infrared_protocols import Command

_LOGGER = logging.getLogger(__name__)

# Electra carrier frequency. pyhvac does not expose the modulation directly,
# so we use the standard AC remote modulation (38 kHz) which is what the
# pyhvac Electra plugin targets.
ELECTRA_MODULATION = 38000


@dataclass(frozen=True, kw_only=True)
class AegAcState:
    """Desired state of the AEG AC at the moment of transmission."""

    mode: str  # off | auto | cool | dry | fan | heat
    temperature: int
    fan: str  # auto | high | medium | low
    swing: str  # off | on


class AegAcCommand(Command):
    """Infrared command for an AEG portable AC.

    Uses pyhvac's Electra plugin to compute raw IR timings and returns
    them as a signed-int list — positive values are pulses (high) in
    microseconds, negative values are spaces (low). This matches the
    `Command.get_raw_timings()` contract from `infrared-protocols`
    (the library bundled with HA's `infrared` building block).
    """

    def __init__(self, *, state: AegAcState, repeat_count: int = 0) -> None:
        super().__init__(modulation=ELECTRA_MODULATION, repeat_count=repeat_count)
        self._state = state
        self._cached: list[int] | None = None

    @property
    def state(self) -> AegAcState:
        return self._state

    def get_raw_timings(self) -> list[int]:
        """Return signed mark/space microsecond timings."""
        if self._cached is not None:
            return list(self._cached)

        # Imported lazily so that import errors only surface at send time
        # (and don't break the integration's setup if pyhvac is missing).
        from pyhvac.plugins.aeg import PluginObject as AegPluginObject

        plugin = AegPluginObject()
        if not plugin.MODELS:
            raise RuntimeError("pyhvac AEG plugin exposes no models")
        # All registered AEG plugin models route to the Electra encoder.
        # Pick the first available class — the choice does not matter as
        # long as it is the Electra subclass.
        hvac_cls = next(iter(plugin.MODELS.values()))
        hvac = hvac_cls()

        hvac.set_mode(self._state.mode)
        if self._state.mode != "off":
            hvac.set_temperature(int(self._state.temperature))
            # Bypass pyhvac.set_fan() — at 0.1.x it writes to the "mode"
            # slot instead of "fan" and validates against the wrong
            # capability list. Drive the staging dict directly with
            # validated values via _stage().
            self._stage(hvac, "fan", self._state.fan)
            # Swing is a deliberate write-through, bypassing _stage().
            # pyhvac's Electra capabilities advertise ["off", "on"] but
            # IRGHVAC's trans_swing() only recognises {"off", "auto",
            # "auto high", ...} — _stage() would accept "on" and the
            # encoder would silently drop the swing bit. AegAcState.swing
            # is therefore already pre-mapped by SWING_TO_PYHVAC to a
            # value trans_swing() understands ("off" or "auto"); pass it
            # straight through without re-translation.
            hvac.to_set["swing"] = self._state.swing

        frames = hvac.build_ircode()
        flat = self._flatten_timings(frames, hvac)
        if not flat:
            raise RuntimeError("pyhvac produced an empty timing list")

        timings = self._sign_timings(flat)
        if not timings:
            raise RuntimeError(
                "pyhvac timings could not be normalised after signing"
            )

        self._cached = timings
        return list(timings)

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _stage(hvac: Any, capability: str, value: str) -> None:
        """Stage a capability change in pyhvac's `to_set` dict, validated."""
        allowed = hvac.capabilities.get(capability)
        if not allowed:
            return
        if value not in allowed:
            value = allowed[0]
        hvac.to_set[capability] = value

    @staticmethod
    def _flatten_timings(frames: Any, hvac: Any) -> list[int]:
        """Coerce pyhvac output to a flat int list, signs preserved.

        pyhvac is heterogeneous: some encoders return raw timing buffers
        from `build_ircode()`, others return byte-frame sequences that
        need to be expanded with `to_lirc(frames)`. We handle both paths.
        """
        flat = AegAcCommand._flatten_ints(frames)

        # Heuristic: a "raw timings" list contains values that look like
        # microseconds (well above 255). A "frames" list of byte values
        # is bounded to 0..255. If we see anything > 255 anywhere, treat
        # the list as raw timings.
        if any(abs(v) > 255 for v in flat):
            return [int(v) for v in flat if v]

        # Otherwise: round-trip through the encoder's to_lirc(frames).
        try:
            lirc = hvac.to_lirc(frames)
        except Exception as err:  # pragma: no cover - defensive
            raise RuntimeError(
                f"pyhvac.to_lirc() failed for AEG state: {err}"
            ) from err
        return [int(v) for v in AegAcCommand._flatten_ints(lirc) if v]

    @staticmethod
    def _flatten_ints(value: Any) -> list[int]:
        """Recursively flatten arbitrary nested iterables to a list of ints.

        Recurses through anything iterable so SWIG-returned vector types
        (`std::vector<int>` exposed via SwigPyObject) are unpacked just
        like a plain Python list. Strings and bytes are intentionally
        treated as scalars to avoid yielding individual characters.
        """
        out: list[int] = []
        if isinstance(value, bool):
            return out
        if isinstance(value, (int, float)):
            out.append(int(value))
            return out
        if isinstance(value, (str, bytes, bytearray)):
            return out
        try:
            iterator = iter(value)
        except TypeError:
            return out
        for item in iterator:
            out.extend(AegAcCommand._flatten_ints(item))
        return out

    @staticmethod
    def _sign_timings(flat: list[int]) -> list[int]:
        """Apply the pulse/space sign convention expected by infrared_protocols.

        Positive values are pulses (high) in microseconds, negative values
        are spaces (low). pyhvac's `to_lirc` emits all-positive LIRC-style
        timings (alternating mark/space); some IRGHVAC paths already use
        signs. We preserve any existing signs, otherwise negate every odd
        index (the spaces).
        """
        if not flat:
            return []
        if any(v < 0 for v in flat):
            # Already signed; drop zero-width entries.
            return [v for v in flat if v != 0]
        signed: list[int] = []
        for idx, value in enumerate(flat):
            if value <= 0:
                continue
            signed.append(value if idx % 2 == 0 else -value)
        return signed
