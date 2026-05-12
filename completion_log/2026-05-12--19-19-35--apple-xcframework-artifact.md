# Apple XCFramework Artifact

## Summary

Implemented the `apple-xcframework` derived artifact, wired it through CD target selection and the reusable build workflow, added XCFramework manifest support, documented Xcode link settings, and marked `specs/010-apple-xcframework-artifact.md` complete.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/test_resolve_build_targets.py .github/scripts/test_create_apple_universal_static_artifact.py .github/scripts/test_create_apple_xcframework_artifact.py`
- `python3 .github/scripts/test_resolve_build_targets.py`
- `python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- `python3 .github/scripts/test_create_apple_xcframework_artifact.py`
- `python3 .github/scripts/resolve_build_targets.py --targets apple-xcframework --json`
- `python3 .github/scripts/resolve_build_targets.py --targets all --json`
- Ruby YAML parse for `.github/workflows/*.yml` and `.github/actionlint.yaml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml`
- `git diff --check`

## Issues

- A full ONNX Runtime Apple CI build was not completed locally before this log was written. The real workflow packager now blocks upload unless the macOS XCFramework slice passes the clang++ consumer smoke test with the macOS SDK.
