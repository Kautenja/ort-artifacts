# Execution Provider Workflow Checkboxes

## Summary

Completed `specs/006-execution-provider-workflow-checkboxes.md`.

Changes:
- Added `enable-xnnpack`, `enable-openvino`, `enable-directml`, `enable-coreml`, and `enable-nnapi` boolean inputs to `.github/workflows/cd.yml`.
- Added matching workflow-call inputs to `.github/workflows/_build.yml` and passed them from both Debug and Release CD jobs.
- Updated the target resolver to preserve current default target arguments while removing disabled provider flags only from compatible targets.
- Added notices when an enabled provider has no compatible selected target.
- Kept OpenVINO setup steps gated on the effective `matrix.args` value.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- Ruby YAML parse for `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- `actionlint` 1.7.12 for `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- Extracted `_build.yml` resolver tests for default arguments, disabled providers, incompatible provider selections, all-provider-off baseline args, and representative platform targets.
- Representative `./build.sh --dry-run` commands for Linux, macOS, iOS simulator, Windows, and Android provider argument shapes.
- `rg` check for OpenVINO setup gating on `matrix.args`
- `git diff --check`

## Issues

- GitHub Actions builds were not dispatched from the local loop. The workflows are expected to run after push.
