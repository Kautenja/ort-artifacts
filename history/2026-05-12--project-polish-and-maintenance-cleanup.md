# Project Polish and Maintenance Cleanup

## Summary

Refreshed the README for the current checkbox-based CD workflow, provider toggles, reduced-operator inputs, target matrix, Ralph/spec records, local validation, and patch maintenance. Cleaned ignored local runtime artifacts and documented root cleanup decisions without changing build targets, workflow inputs, artifact naming, patch contents, or release behavior.

## Decisions

- Kept `.specify/memory/constitution.md` and `AGENTS.md` as the source of truth for agent workflow rules; the README now links to and summarizes those records instead of duplicating them wholesale.
- Replaced stale README target selection guidance with the current `target-all` default and exact target checkbox behavior.
- Documented provider checkboxes as global inputs that only apply to compatible targets.
- Updated reduced-operator examples to use current workflow inputs: `target-all=false` and an exact target checkbox.
- Changed `.gitignore` from two exact generated prompt names to `/PROMPT_*.md`, matching the Ralph loop's generated root prompt artifact pattern.
- Left `logs/.gitkeep` in place so the ignored runtime log directory remains visible.
- Preserved `openvino_tbb_libs_Debug.txt` and `openvino_tbb_libs_Release.txt` after a reference check found `CMakeLists.txt` reads `openvino_tbb_libs_${OPENVINO_BUILD_CONFIG}.txt` for OpenVINO/TBB packaging.

## Cleanup Inventory

- `PROMPT_build.md`: generated Ralph prompt file, ignored by git, removed from the local working tree.
- `PROMPT_plan.md`: generated Ralph prompt file, ignored by git, removed from the local working tree.
- `logs/.gitkeep`: tracked placeholder, retained.
- `logs/ralph_codex_build_iter_1_20260512_133053.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_1_20260512_133053.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_iter_2_20260512_134452.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_2_20260512_134452.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_iter_3_20260512_135804.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_3_20260512_135804.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_session_20260512_133053.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_build_iter_1_20260512_170036.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_1_20260512_170036.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_iter_2_20260512_171915.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_2_20260512_171915.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_iter_3_20260512_172757.log`: generated runtime log, ignored by git, removed locally.
- `logs/ralph_codex_output_iter_3_20260512_172757.txt`: generated runtime output, ignored by git, removed locally.
- `logs/ralph_codex_build_session_20260512_170036.log`: generated runtime log, ignored by git, removed locally.
- `.github/scripts/__pycache__/generate_manifest.cpython-314.pyc`: generated Python bytecode, ignored by git, removed locally after validation.
- `.github/scripts/__pycache__/validate_required_operators_config.cpython-314.pyc`: generated Python bytecode from previous validation, ignored by git, removed locally.
- `openvino_tbb_libs_Debug.txt`: tracked CMake input for OpenVINO/TBB packaged library names, retained.
- `openvino_tbb_libs_Release.txt`: tracked CMake input for OpenVINO/TBB packaged library names, retained.

Reference checks used `git ls-files`, ignored-file listing, and `rg` across README, workflows, scripts, specs, history, completion logs, and CMake sources before any cleanup decision.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `git diff --check`
- `rg` verified README no longer references removed manual workflow inputs.
- Python comparison verified README target table entries match CD target checkbox inputs and provider documentation includes current provider inputs.

## Issues

- Workflow YAML and `actionlint` were not run because this cleanup did not change workflow files.
- No live GitHub Actions build was dispatched locally. The change is documentation and housekeeping only.
