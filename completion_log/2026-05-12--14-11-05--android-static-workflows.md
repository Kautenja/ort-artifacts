# Android Static Artifact Workflows

## Summary

Completed `specs/003-android-static-workflows.md`.

- Added active Android static build targets for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- Added all four Android targets to CD workflow dispatch choices.
- Scoped Java, Android SDK, and NDK setup to Android targets and verified SDK/NDK environment availability before `build.sh`.
- Added Android ABI validation and ABI-derived architecture mapping in `build.sh` and CMake.
- Documented native CMake/JNI consumption and the exclusion of Java bindings, `onnxruntime4j`, and AAR packaging.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `./build.sh --dry-run --static --android --android_abi arm64-v8a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi armeabi-v7a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi x86_64 --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi x86 --xnnpack --nnapi -N`
- Workflow YAML parsed successfully for `_build.yml`, `cd.yml`, and `_publish.yml`.
- Workflow `run` snippets passed `bash -n` after GitHub expression substitution.
- Android workflow matrix and CD preset assertions passed.
- Local CMake configure checks passed for all four Android ABIs using the local SDK/NDK installation.
- Generated ExternalProject commands were inspected for each ABI and include Android platform, ABI, NDK toolchain, XNNPACK, and NNAPI flags.
- Representative Android archive and manifest test passed for all four target names with `libonnxruntime.a`, a public header, and a CMake dependency file.
- `git diff --check`

## Limitations

- Full Android ONNX Runtime compilation was not run locally because it would require expensive per-ABI native builds. The local equivalent validation covered the workflow matrix, `build.sh` argument plumbing, CMake generation, generated ExternalProject configure commands, archive shape, and manifest behavior.
- `gh` is not installed on this machine, so no workflow dispatch was launched from the loop. Runner-level validation can be dispatched with:

```bash
gh workflow run cd.yml --repo Kautenja/ort-artifacts --ref ralph-dev -f onnxruntime-ref=v1.22.2 -f target-preset=all -f target-custom=android -f buildtype=Release -f publish=false
```
