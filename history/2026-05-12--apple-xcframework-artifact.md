# Apple XCFramework Artifact

## Summary

Added a derived `apple-xcframework` artifact that packages the existing iOS device static artifact plus the iOS simulator and macOS universal static artifacts into `onnxruntime.xcframework`.

## Decisions

- Kept raw static Apple artifacts unchanged and modeled `apple-xcframework` as a derived target in `.github/scripts/resolve_build_targets.py`.
- Selecting `apple-xcframework` schedules `ios-aarch64-static`, `ios-simulator-universal-static`, and `macos-universal-static`; those universal targets still expand to their architecture-specific source builds.
- Added `.github/scripts/create_apple_xcframework_artifact.py` so local fixtures and GitHub Actions use the same extraction, header comparison, reduced-operator metadata comparison, `lipo`, `xcodebuild`, and consumer smoke-test logic.
- The packager fails before upload if the macOS XCFramework slice cannot compile and link a minimal consumer that includes ONNX Runtime headers and references `OrtGetApiBase`.
- Documented default Apple static link settings in both the repository README and the packaged XCFramework README: `Foundation.framework`, `CoreML.framework`, `Accelerate.framework`, `-lc++`, iOS 15.0, and macOS 13.3.
- Extended `generate_manifest.py` with an `apple-xcframework` artifact type so release manifests record the XCFramework archive, SHA256, slice identifiers, platforms, variants, architectures, and header paths.

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

- No full ONNX Runtime Apple release build was completed locally before this history entry. The workflow now gates the real macOS slice with the same clang++ macOS consumer link smoke test before uploading the XCFramework artifact.
- The local XCFramework functional test uses real Apple SDKs and Mach-O fixture static libraries to validate `xcodebuild -create-xcframework`, library identifiers, `lipo -info`, manifest generation, and the macOS/iOS simulator consumer compile-link path.
