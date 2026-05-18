<p align="center">
  <img src="https://raw.githubusercontent.com/quadjojo/ha-aeg-infrared/main/icon.png" width="96" height="96" alt="AEG Infrared logo">
</p>

# AEG Infrared for Home Assistant

A HACS-installable custom integration that exposes AEG **Chillflex Pro** mobile air conditioners (e.g. **AXP26U558HW**, **AXP34U338CW**, **AXP26U338CW**) as a native Home Assistant `climate` entity, sending IR commands through the new **Infrared building block** introduced in Home Assistant **2026.4**.

> **Heads-up — vibecoded.** Scaffolded with AI assistance. The **AXP26U558HW** (heat-pump) variant has been hardware-verified end-to-end — mode, temperature, fan and swing all confirmed working on the physical unit. The two cool-only siblings share the encoder but have not yet been independently tested. Bug reports and hardware confirmations welcome.

> **Maintenance status — community-driven.** The original author published this as a one-shot scratch and is **not actively maintaining it**. Issues and pull requests from anyone are welcome and will land as long as a reviewer (you, me, anyone with `repo:write`) signs off. If you'd like to help maintain or co-own this, open an issue or start a [discussion](https://github.com/quadjojo/ha-aeg-infrared/discussions) — I'm happy to add maintainers.

## What it does

Wraps an AEG portable AC behind a standard `climate.*` entity:

| Capability | Values |
|---|---|
| HVAC modes | `off`, `auto`, `cool`, `dry`, `fan_only`, `heat`* |
| Fan modes | `auto`, `low`, `medium`, `high`† |
| Swing | `off`, `on` |
| Target temperature | 16–32 °C in 1 °C steps |

\* On cool-only units the `heat` frame is transmitted but ignored by the AC.<br>
† While the HVAC mode is `off` or `auto`, the fan selector is locked to `auto` — the AC chooses the fan speed itself in those modes, just like the physical remote.

## Prerequisites

1. **Home Assistant 2026.4 or newer** — the integration depends on the native `infrared` building block.
2. An **infrared emitter entity** in HA, typically provided by an ESPHome-flashed IR proxy (the [Seeed Studio XIAO IR Mate](https://www.seeedstudio.com/) is the reference device, but anything that registers as an `infrared.*` entity will work).
3. The **Infrared integration** itself configured and bound to your emitter.
4. **HACS** installed (only required if installing via HACS; manual install works without it).

## Installation

### Option A — via HACS

1. HACS → **Integrations** → top-right menu → **Custom repositories**.
2. Repository URL: `https://github.com/quadjojo/ha-aeg-infrared`. Category: **Integration**.
3. Search for *AEG Infrared*, install, and **restart Home Assistant**.
4. Open **Settings → Devices & services → Add integration**, pick **AEG Infrared**.
5. Choose your model and the infrared emitter that should radiate the commands.

### Option B — manual install

```bash
cd /path/to/your/homeassistant/config
git clone https://github.com/quadjojo/ha-aeg-infrared.git
cp -r ha-aeg-infrared/custom_components/aeg_infrared custom_components/
```

Restart Home Assistant, then add the integration from the UI as in step 4 above.

## Architecture

```
┌─────────────────────────┐    async_send_command(Command)    ┌──────────────┐
│ aeg_infrared (climate)  │ ─────────────────────────────────►│   infrared   │
│  ClimateEntity          │                                   │ (HA core)    │
│  → AegAcCommand         │                                   └──────┬───────┘
│    (extends Command)    │                                          │
└─────────────────────────┘                                          ▼
            │                                          ┌─────────────────────────┐
            │   pyhvac.plugins.aeg → Electra encoder   │ ESPHome IR proxy        │
            └─────────────────────────────────────────►│ (e.g. XIAO IR Mate)     │
                                                       └─────────────────────────┘
```

* The climate entity holds the **desired** state. Every change builds a fresh `AegAcCommand` and calls `infrared.async_send_command(...)`.
* `AegAcCommand` is an `infrared_protocols.Command` whose `get_raw_timings()` returns a signed `list[int]` of microsecond timings (positive = pulse, negative = space) by routing through `pyhvac`'s Electra encoder.
* The `infrared` building block hands the timings to the selected ESPHome proxy via the native API.
* `assumed_state = True` because IR is one-way — the AC never reports back.

## Supported models

| Model | Type | Status |
|---|---|---|
| `Chillflex Pro AXP26U558HW` | heat-pump | ✅ Hardware-verified (mode, temperature, fan, swing) |
| `Chillflex Pro AXP34U338CW` | cool-only | Implemented, not yet hardware-tested |
| `Chillflex Pro AXP26U338CW` | cool-only | Implemented, not yet hardware-tested |

All listed models share the Electra IR protocol; the suffix `HW` indicates a heat-pump variant that additionally honours the `heat` HVAC mode. Other Chillflex Pro variants are likely to work — open an issue with the model number if you'd like one added.

## Known limitations

* Only `AXP26U338CW` is officially registered in `pyhvac`. The sister models are routed to the same Electra encoder under the assumption they share the protocol; the `AXP26U558HW` confirmation is empirical.
* `pyhvac 0.1.x` has a bug in `set_fan()` (writes to the wrong slot). The integration bypasses it by writing to `pyhvac`'s staging dict directly — see [`commands.py`](custom_components/aeg_infrared/commands.py).
* On HA restart the last *desired* state is restored but **no IR command is re-sent**, so the integration cannot accidentally toggle the AC on its own.
* Fan and swing changes while the AC is `off` only update the HA-side state; the change is transmitted on the next power-on.
* No code learning. The Electra encoder is generated; if your unit ignores the frames, recording from the original remote is not currently a fallback.

## Troubleshooting

* **AC doesn't react.** Confirm the infrared emitter works at all (e.g. trigger a known-good LG TV command via the `infrared` integration). If the emitter is fine, the encoding is most likely off — please open an issue and attach the output of:
  ```python
  from custom_components.aeg_infrared.commands import AegAcCommand, AegAcState
  cmd = AegAcCommand(state=AegAcState(mode="cool", temperature=22, fan="auto", swing="off"))
  print(cmd.get_raw_timings())  # signed µs ints: + = pulse, - = space
  ```
* **`No infrared transmitter entity found` during setup.** The `infrared` integration is not configured yet, or no emitter has been bound to it. Set that up first.
* **Integration fails to load with an import error for `pyhvac`.** Home Assistant installs the requirement automatically; if it failed, check the HA log around the integration's first load.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. Quick start: open an issue first if your change is non-trivial, otherwise PR straight against `main`. CI runs Python syntax + JSON validation on every PR.

Particularly welcome:

* Hardware reports (works / doesn't work, with model number)
* Recordings of original-remote IR captures for protocol verification
* Adding more Chillflex Pro / Electrolux portable AC variants
* Translations beyond English and German
* Anyone willing to be added as a maintainer

## Credits

* [Home Assistant 2026.4 Infrared building block](https://www.home-assistant.io/integrations/infrared/) — the native abstraction this integration plugs into.
* [`infrared-protocols`](https://github.com/home-assistant-libs/infrared-protocols) — `Command` base class and the signed-int timing contract.
* [`pyhvac`](https://github.com/frawau/pyhvac) by François Wautier — Electra protocol encoder.
* [`lg_infrared`](https://github.com/home-assistant/core/tree/dev/homeassistant/components/lg_infrared) — architectural reference for this integration.

## License

[MIT](LICENSE)
