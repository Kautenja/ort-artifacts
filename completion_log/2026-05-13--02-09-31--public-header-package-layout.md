# Public Header Package Layout

## Summary

- Replaced raw ONNX Runtime header tree installation with curated root-level public headers in `src/static-build/CMakeLists.txt`.
- Added `.github/scripts/validate_public_headers.py` and CI coverage before archive upload.
- Updated Apple XCFramework and Windows test fixtures to use the root-level package header layout.
- Documented the static artifact header layout in `README.md`.

## Validation

- `python3 .github/scripts/test_validate_public_headers.py`
- `python3 .github/scripts/test_slim_windows_artifact.py`
- `python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- `python3 .github/scripts/test_create_apple_xcframework_artifact.py`
- `python3 .github/scripts/test_resolve_build_targets.py`
- `python3 -m unittest discover -s .github/scripts -p 'test_*.py'`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py .github/scripts/validate_public_headers.py .github/scripts/test_validate_public_headers.py`
- `./build.sh --dry-run`
- `./build.sh --dry-run --static --iphoneos -A aarch64 --coreml --xnnpack -N`
- `./build.sh --dry-run --static --android --android_abi arm64-v8a --xnnpack --nnapi -N`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file) }' .github/workflows/cd.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml`
- `git diff --check`
- Local fake-source CMake configure/build/install validating curated root-level headers and cleanup of raw upstream header directories.

## Notes

- No full ONNX Runtime iOS or Android build was run locally because that would require fetching/building the upstream source and platform toolchains. The targeted dry-runs, validator fixtures, and CMake install fixtures verify the changed packaging behavior.
