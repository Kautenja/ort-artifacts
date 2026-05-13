# Android API 24 Static Artifacts

## Summary

- Completed Android API 24 static artifact support for ONNX Runtime `v1.22.0`.
- Added API 24 defaults, Android static PIC/no-LTO/emulated-TLS flags, x86 MLAS patching, Android archive validation, CD workflow integration, and README/spec completion notes.
- Validated the staged downstream Android SDK at `minSdk 24` with release AAR generation and connected instrumentation tests.

## Validation

- `python3 -m unittest discover -s .github/scripts -p 'test_*.py'`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py .github/scripts/validate_public_headers.py .github/scripts/validate_android_static_archive.py`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `./build.sh --dry-run`
- Android API 24 dry-runs for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file) }' .github/workflows/cd.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml`
- `git diff --check`
- Local `v1.22.0` Android static artifact builds and validator smoke tests for all four Android ABIs.
- Downstream `./main.sh release` and `./main.sh test` in the staged SDK; instrumentation reported `OK (157 tests)`.

## Notes

- The unavailable downstream path was replaced with a temp copy of the local backup at `/tmp/sensory-face-android-api24.i1Essj`.
- The local old shared package was ONNX Runtime `1.15.1`, not the expected `v1.22.0`; exact historical shared package API/NDK flags were not recoverable.
- The GitHub Release CD workflow was not dispatchable locally because `gh` was not installed; local CD-equivalent Android builds and the new workflow validator covered the release path.
