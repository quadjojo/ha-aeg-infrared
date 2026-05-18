# Contributing to AEG Infrared

Thanks for your interest in this integration. The original author is not
actively maintaining the project, so contributions land via community PRs
plus whoever currently has review rights. This document explains how to
get a change in safely.

## Ways to help

| What | How |
|---|---|
| Confirm a model works | Open a [Hardware report](.github/ISSUE_TEMPLATE/hardware_report.yml) issue |
| Report a bug | Open a [Bug report](.github/ISSUE_TEMPLATE/bug_report.yml) issue with the full traceback from the HA log |
| Suggest a feature | Open a [Feature request](.github/ISSUE_TEMPLATE/feature_request.yml) — small ones can be proposed directly as a PR |
| Add a model variant | Edit `custom_components/aeg_infrared/const.py` (`SUPPORTED_MODELS`, `PYHVAC_MODEL_FALLBACKS`), add a row to the README table, send a PR |
| Add a translation | Drop a JSON file in `custom_components/aeg_infrared/translations/` mirroring `en.json` |
| Be added as a maintainer | Drop a note on a [discussion](https://github.com/quadjojo/ha-aeg-infrared/discussions) — happy to share keys |

## Repo layout

```
custom_components/aeg_infrared/
├── __init__.py        # entry point, sets up the climate platform
├── manifest.json      # version, dependencies, requirements
├── const.py           # model list, mappings, capability constants
├── commands.py        # AegAcCommand → infrared_protocols.Command (Timing pairs)
├── config_flow.py     # picks an emitter via async_get_emitters()
├── entity.py          # base entity that tracks emitter availability
├── climate.py         # ClimateEntity itself
├── strings.json       # source-of-truth UI strings (English)
└── translations/      # localised UI strings
hacs.json              # HACS metadata
icon.svg               # repo + integration logo
CHANGELOG.md           # Keep a Changelog format
```

## Local sanity checks

The integration runs inside Home Assistant; full integration tests need a
running HA. The change set you ship in a PR should at minimum pass:

```bash
python3 -c "
import ast, json, pathlib
root = pathlib.Path('.')
for p in sorted(root.rglob('*.py')):
    ast.parse(p.read_text())
for p in sorted(root.rglob('*.json')):
    json.loads(p.read_text())
print('ok')
"
```

CI runs the same check on every PR (see `.github/workflows/ci.yml`).

If your change touches the IR encoding path, please also include a small
reproduction in the PR body that shows the timings before/after, e.g.:

```python
from custom_components.aeg_infrared.commands import AegAcCommand, AegAcState
cmd = AegAcCommand(state=AegAcState(mode="cool", temperature=22, fan="auto", swing="off"))
for t in cmd.get_raw_timings()[:8]:
    print(t.high_us, t.low_us)
```

## PR conventions

* **Branch naming:** anything; please don't push to `main` directly.
* **Commits:** keep the title under ~70 chars, focus on *why* in the body.
* **CHANGELOG.md:** add a bullet under `[Unreleased]` describing the user-visible effect.
* **manifest.json `version`:** bump only as part of a release PR. Day-to-day PRs leave it alone.
* **Tests:** none yet; if your change adds one, put it under `tests/` at the repo root.

## Releasing

1. Move the `[Unreleased]` block in `CHANGELOG.md` to a new dated `[X.Y.Z]` block.
2. Bump `version` in `manifest.json` to match.
3. Commit, tag `vX.Y.Z`, push tag.
4. Create a GitHub release with the changelog excerpt as the body. HACS picks it up automatically.

## Code of conduct

Be kind. This is a hobby project people are giving their time to.
