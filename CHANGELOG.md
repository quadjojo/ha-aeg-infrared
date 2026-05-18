# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-05

### Added
- Initial release of the **AEG Infrared** integration for Home Assistant 2026.4+.
- Climate entity for AEG Chillflex Pro mobile air conditioners. Hardware-verified
  on `Chillflex Pro AXP26U558HW`; `AXP34U338CW` and `AXP26U338CW` are routed
  through the same Electra encoder under the assumption they share the protocol.
- Config flow that binds to any infrared emitter exposed by the native
  `infrared` building block (e.g. an ESPHome IR proxy such as the
  Seeed Studio XIAO IR Mate).
- Support for HVAC modes (off / auto / cool / dry / fan_only / heat),
  fan modes (auto / low / medium / high), binary swing on/off, and target
  temperature in the 16–32 °C range.
- Fan selector is locked to `auto` while the HVAC mode is `off` or `auto`,
  mirroring the physical remote's behaviour. The full speed list returns in
  cool / heat / dry / fan_only.
- IR command encoding via `pyhvac`'s Electra plugin, wrapped as an
  `infrared_protocols.Command` whose `get_raw_timings()` returns the
  signed `list[int]` of microsecond pulses/spaces the building block
  expects (positive = pulse, negative = space).
- Workarounds for known `pyhvac 0.1.x` issues: `set_fan()` writes to the
  wrong staging slot (bypassed by direct dict write), and the Electra
  capabilities advertise `swing=["off","on"]` while the underlying
  encoder only honours `{"off","auto",…}` (mapped through to `"auto"`).
- English and German translations.
- Custom icon shipped both at the repo root (referenced from the README via
  an absolute `raw.githubusercontent.com` URL so it renders inside HACS) and
  in `custom_components/aeg_infrared/brand/` (256×256 `icon.png` plus 512×512
  `icon@2x.png`), which Home Assistant 2026.3+ serves through its local
  brands proxy at `/api/brands/integration/aeg_infrared/icon.png` — no PR
  against the central brands repo is required.

[Unreleased]: https://github.com/quadjojo/ha-aeg-infrared/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/quadjojo/ha-aeg-infrared/releases/tag/v0.1.0
