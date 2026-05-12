# Apple Universal Static Artifacts

## Summary

Completed `specs/009-apple-universal-static-artifacts.md`.

Changes:
- Added CD workflow checkboxes for `macos-universal-static` and `ios-simulator-universal-static`.
- Added reusable target resolution that expands universal requests into the required source slice builds while preserving existing architecture-specific and non-Apple target behavior.
- Added a macOS packaging job that downloads the matching source zips, validates layout/header/reduced-ops metadata compatibility, creates the universal static archive with `lipo`, verifies expected architectures, and uploads the derived artifact.
- Updated manifest generation to record artifact name and library directory along with SHA256 and primary library path.
- Documented the universal Apple artifacts and added focused resolver and packaging tests.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/test_resolve_build_targets.py .github/scripts/test_create_apple_universal_static_artifact.py`
- `python3 .github/scripts/test_resolve_build_targets.py`
- `python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- Ruby YAML parse for `.github/workflows/*.yml` and `.github/actionlint.yaml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml`
- `git diff --check`
- Resolver CLI checks for all required target-selection cases.

## Issues

- Full ONNX Runtime Apple CI builds were not dispatched locally. The representative local tests compile tiny macOS and iOS simulator static archives, create universal artifacts with real `lipo`, verify `lipo -info`, and run manifest generation against the resulting archives.
