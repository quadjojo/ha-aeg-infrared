<!--
Thanks for sending a PR. A few quick checks before you mark it ready:

- The CI job runs Python syntax + JSON validation. If it fails, click the
  failed check on the PR page to see why.
- Day-to-day PRs do NOT bump the version in manifest.json. Releases handle that.
- If your change is user-visible, add a bullet under [Unreleased] in CHANGELOG.md.
-->

## What this changes

<!-- One or two sentences. Why, not what. -->

## How it was tested

<!-- Real hardware? Reproduction harness? Just `python3 -c "import ast..."`? -->

## Hardware (if applicable)

- AEG model:
- Integration version base:
- Home Assistant version:
- Infrared emitter / proxy:

## Checklist

- [ ] CI passes
- [ ] CHANGELOG entry added under `[Unreleased]` (if user-visible)
- [ ] Touched English strings have a German equivalent (or vice versa) — `strings.json` and `translations/de.json` stay in sync
- [ ] No secrets, no `.env`, no personal IDs in the diff
