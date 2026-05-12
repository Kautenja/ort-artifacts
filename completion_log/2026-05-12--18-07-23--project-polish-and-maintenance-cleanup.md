# Project Polish and Maintenance Cleanup

## Summary

Completed `specs/008-project-polish-and-maintenance-cleanup.md`.

Changes:
- Refreshed `README.md` for current CD target checkboxes, `target-all`, provider toggles, reduced-operator usage, target notes, Ralph records, validation, and patch maintenance.
- Narrowed generated prompt ignores to `/PROMPT_*.md`.
- Removed ignored local Ralph prompt files, runtime logs, and Python bytecode from the working tree while preserving required `.gitkeep` placeholders.
- Classified OpenVINO/TBB probe-looking files as required tracked CMake inputs and retained them.

## Cleanup Inventory

- `PROMPT_build.md`: generated, ignored, removed locally.
- `PROMPT_plan.md`: generated, ignored, removed locally.
- `logs/.gitkeep`: tracked placeholder, retained.
- `logs/ralph_codex_build_iter_1_20260512_133053.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_1_20260512_133053.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_iter_2_20260512_134452.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_2_20260512_134452.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_iter_3_20260512_135804.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_3_20260512_135804.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_session_20260512_133053.log`: generated, ignored, removed locally.
- `logs/ralph_codex_build_iter_1_20260512_170036.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_1_20260512_170036.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_iter_2_20260512_171915.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_2_20260512_171915.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_iter_3_20260512_172757.log`: generated, ignored, removed locally.
- `logs/ralph_codex_output_iter_3_20260512_172757.txt`: generated, ignored, removed locally.
- `logs/ralph_codex_build_session_20260512_170036.log`: generated, ignored, removed locally.
- `.github/scripts/__pycache__/generate_manifest.cpython-314.pyc`: generated, ignored, removed locally after validation.
- `.github/scripts/__pycache__/validate_required_operators_config.cpython-314.pyc`: generated, ignored, removed locally.
- `openvino_tbb_libs_Debug.txt`: tracked CMake input referenced by `CMakeLists.txt`, retained.
- `openvino_tbb_libs_Release.txt`: tracked CMake input referenced by `CMakeLists.txt`, retained.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `git diff --check`
- README stale-input check: no `target-preset` or `target-custom` references remain in `README.md`.
- README matrix check: target table entries match `.github/workflows/cd.yml` target checkbox inputs and provider input names are documented.

## Issues

- Workflow YAML parsing and `actionlint` were not required because no workflow files changed.
- No live GitHub Actions run was dispatched from the local loop.
