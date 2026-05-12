# Checkbox Target Workflow Dispatch

## Summary

Replaced the manual CD target preset and custom substring filter with boolean target checkboxes. The CD workflow now assembles either `all` or a comma-separated exact target list, and the reusable build workflow validates that list before expanding a dynamic matrix containing only selected active targets.

## Decisions

- Kept `target-all` defaulting to `true` to preserve the previous manual workflow default of building every active target.
- Named individual checkbox inputs after the exact active target identifiers so the UI selection maps directly to artifact and manifest target names.
- Moved target selection validation into `_build.yml` so `Both` buildtype runs validate target selection separately for Debug and Release.
- Rejected unknown target names in `_build.yml`, which removes substring matching from the build decision path.
- Preserved existing target names, build arguments, artifact names, archive names, reduced-operator metadata behavior, and publish wiring.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- Ruby YAML parse for `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- Downloaded `actionlint` 1.7.12 release binary and linted `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- Extracted and executed the `_build.yml` target resolver for `all`, single target, multiple targets, duplicate target, substring, and empty target cases.
- Extracted and executed the `cd.yml` selector for `target-all`, single target, multiple targets, and empty target checkbox cases.
- `rg` verified `target-preset`, `target-custom`, and old substring target matching no longer appear in workflow files.
- `git diff --check`

## Issues

- No live GitHub Actions build was dispatched locally. The workflow syntax and target-selection behavior were validated locally; runner-specific builds will execute after push.
