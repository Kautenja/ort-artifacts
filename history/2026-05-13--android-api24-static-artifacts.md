# Android API 24 Static Artifacts

## Decisions

- Defaulted Android builds to API 24 in `build.sh`, `CMakeLists.txt`, and target resolution for all four Android static workflow targets.
- Added Android static build flags for PIC, disabled LTO for static Android archives, and applied `-femulated-tls` for API levels below 29.
- Preserved `android-x86-static` by adding a `v1.22` patch that removes the Android x86 MLAS AVX assembly path and uses SSE/generic dispatch instead.
- Added an Android static archive validator that rejects `__tls_get_addr` and unsupported ELF TLS relocations, allows `__emutls_*`, and runs an NDK shared-library link smoke test with `ANDROID_PLATFORM=android-24`.
- Wired the validator into CD after public-header validation and before artifact upload.
- Added a `v1.22.0`-only Eigen mirror patch because upstream `v1.22.0` fetched a stale GitLab archive with a mismatched hash.

## Lessons Learned

- The local downstream backup's old shared ONNX Runtime package is `1.15.1` with `ORT_API_VERSION 15`; the exact expected `v1.22.0` shared package and historical Android API/NDK flags were not recoverable locally.
- Shared delivery avoided the downstream static archive link problem because consumers linked only against a prebuilt `libonnxruntime.so`; static delivery exposed API and PIC mistakes at the downstream JNI shared-library link.
- Android API 35 emulator Gradle result collection reported an aborted zero-test `connectedDebugAndroidTest`, but direct instrumentation of the same test APK completed successfully with `OK (157 tests)`. The temporary downstream validation wrapper was adjusted to build/install the test APK and invoke `am instrument` directly.

## Validation Performed

- `python3 -m unittest discover -s .github/scripts -p 'test_*.py'`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py .github/scripts/validate_public_headers.py .github/scripts/validate_android_static_archive.py`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `./build.sh --dry-run`
- `./build.sh --dry-run --static --android --android_api 24 --android_abi arm64-v8a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_api 24 --android_abi armeabi-v7a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_api 24 --android_abi x86_64 --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_api 24 --android_abi x86 --xnnpack --nnapi -N`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file) }' .github/workflows/cd.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml`
- `git diff --check`
- Local ONNX Runtime `v1.22.0` Android static builds for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- Public-header validation and full Android static archive validation for each built ABI, including API 24 NDK shared-library link smoke tests.
- Downstream staged SDK release build at `/tmp/sensory-face-android-api24.i1Essj` with all four ABIs enabled and `minSdk 24`.
- Downstream staged SDK test run at `/tmp/sensory-face-android-api24.i1Essj` using direct `am instrument`; result was `OK (157 tests)`.
- Release/debug AAR inspection confirmed all four `libsensoryface.so` slices were packaged and no `libonnxruntime.so` or `libonnxruntime.a` was included.

## Issues Encountered

- The expected downstream checkout path was not present; validation used the local backup copied to `/tmp/sensory-face-android-api24.i1Essj`.
- `gh` was not installed, so the GitHub Release CD workflow could not be dispatched from this machine. The same build path was validated locally with CD-equivalent Android target builds and the workflow now runs the archive validator before upload.
- Android Gradle plugin 8.1 on the API 35 emulator lost the final instrumentation watcher result after all tests passed, producing an `ABORTED` zero-test Gradle report. Direct device instrumentation completed normally and was used for the downstream `./main.sh test` validation wrapper.
