# Single Visible CD Workflow

## Summary

Consolidated GitHub Actions to one visible workflow file: `.github/workflows/cd.yml`.

## Decisions

- Removed `.github/workflows/_build.yml` and `.github/workflows/_publish.yml` so GitHub does not show `Build` or `Publish` as sidebar workflows.
- Kept the build functionality as first-class CD jobs: target validation, platform builds, Apple universal packaging, and Apple XCFramework packaging now run directly inside `CD`.
- Extended `.github/scripts/resolve_build_targets.py` to expand `Debug`, `Release`, and `Both` into matrix entries. `Both` emits Debug entries and Release entries while keeping target names, provider filtering, derived Apple targets, and artifact-name inputs unchanged.
- Confirmed local active callers did not require `_publish.yml`, and `_build.yml` was only an internal CD implementation detail. `Build` remains required as job logic, but not as a separate top-level workflow.
- Left manifest generation support intact.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/resolve_build_targets.py .github/scripts/validate_required_operators_config.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_resolve_build_targets.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_create_apple_xcframework_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_slim_windows_artifact.py`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file); puts "parsed #{file}" }' .github/workflows/*.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml`
- `git diff --check`
- Local workflow checks confirmed only `.github/workflows/cd.yml` remains, no `workflow_call` remains under `.github/workflows`, no local workflow calls remain, and no active workflow has `name: Build` or `name: Publish`.
- Local input-count check reported 24 workflow dispatch inputs.
- Empty target selection fails in `.github/scripts/resolve_build_targets.py` before platform setup.
- Matrix assertions verified `Debug`, `Release`, and `Both` expansion paths.
- Representative artifact-name assertions matched the prior `ort-<ref>-<target>-<buildtype>` and `ort-<ref>-<target>-ops-<sha>-<buildtype>` forms.

## Issues

- No local platform builds were run because this change is workflow orchestration only and the local machine cannot represent all GitHub-hosted Linux, Windows, Android, and Apple runner combinations.
