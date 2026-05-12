# Checkbox Target Workflow Dispatch

## Summary

Implemented checkbox-based manual target selection for the CD workflow. The old preset dropdown and custom substring filter are gone, `target-all` and all active target checkboxes are exposed, and `_build.yml` now validates exact target selections before creating the build matrix.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- Ruby YAML parse for workflow files
- `actionlint` 1.7.12 for workflow expression and schema checks
- Local target-selection checks covered all targets, single target, multiple targets, duplicate target, rejected substring target, empty target, and CD checkbox assembly.
- `git diff --check`

## Limitations

No live GitHub Actions run was started from this local environment.
