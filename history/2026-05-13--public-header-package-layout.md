# Public Header Package Layout

## Decisions

- Replaced the static-build raw `${ONNXRUNTIME_SOURCE_DIR}/include/onnxruntime` directory install with an explicit root-level public header list.
- Kept the required session headers and `cpu_provider_factory.h` for all static artifacts.
- Added enabled provider headers for CoreML, NNAPI, DirectML, and OpenVINO, with optional support for legacy GPU/DNNL/ROCm public headers if those builds are enabled directly.
- Cleared the staged `include/onnxruntime` directory before installing curated headers and added a final cleanup for unexpected root headers plus nested `core` and `session` directories.
- Added a reusable staged-artifact validator and ran it in CD before archive creation.

## Lessons Learned

- The existing raw tree copy made mobile artifacts expose upstream source paths rather than the compact client package layout expected by downstream consumers.
- Apple derived artifact tests needed to model the real static artifact include root (`onnxruntime/include/onnxruntime/*.h`) so XCFramework smoke tests keep matching release packages.
- A CMake fixture with a fake upstream install rule is useful for proving the wrapper removes upstream raw headers without fetching ONNX Runtime.

## Validation Performed

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
- Local CMake fixture configure/build/install against a fake ONNX Runtime source tree with CoreML and NNAPI headers.
- Local CMake fixture proving raw upstream root and nested headers are removed before final packaging.

## Issues Encountered

- The first fake CMake fixture omitted `CMAKE_DEBUG_POSTFIX`, which the static-build wrapper expects from the real top-level build. Re-running the fixture with `-DCMAKE_DEBUG_POSTFIX=d` matched normal build configuration and passed.
- `actionlint` was not installed locally. Running it through `go run` required network approval, then passed.
