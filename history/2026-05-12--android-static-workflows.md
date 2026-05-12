# Android Static Artifact Workflows

## Summary

- Enabled Android native static artifact workflow targets for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- Added all four Android targets to manual CD dispatch presets.
- Scoped Android SDK, Java, and NDK setup to Android targets and added an SDK/NDK verification step.
- Added Android ABI validation and ABI-to-architecture mapping in `build.sh` and CMake.
- Documented that Android artifacts are native static archives for downstream CMake/JNI integration, not Java bindings or AAR packages.

## Decisions

- Use target names based on Android ABI names: `android-arm64-v8a-static`, `android-armeabi-v7a-static`, `android-x86_64-static`, and `android-x86-static`.
- Keep Android execution providers to XNNPACK and NNAPI for this phase.
- Treat `--android_abi` as the source of truth for Android architecture selection; `build.sh` and CMake derive `TARGET_ARCH` from it.
- Keep OpenVINO, DirectML, Core ML, and host platform flags out of Android CMake configuration.
- Continue using the existing zip upload and manifest generation flow because it is target-name agnostic and recognizes `libonnxruntime.a`.

## Lessons Learned

- Host platform detection can leak macOS deployment flags into Android cross-compile configuration unless Android is explicitly excluded from native Darwin/Windows blocks.
- `android-actions/setup-android` and `nttld/setup-ndk` should be gated by `contains(matrix.target, 'android')` so new ABI rows do not need repeated condition updates.
- A representative archive test is enough to prove manifest naming and static archive recognition without changing the manifest generator.

## Validation Performed

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `./build.sh --dry-run --static --android --android_abi arm64-v8a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi armeabi-v7a --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi x86_64 --xnnpack --nnapi -N`
- `./build.sh --dry-run --static --android --android_abi x86 --xnnpack --nnapi -N`
- Ruby YAML parse for `.github/workflows/_build.yml`, `.github/workflows/cd.yml`, and `.github/workflows/_publish.yml`.
- Extracted workflow `run` snippets and checked them with `bash -n` after substituting GitHub expressions.
- Ruby assertion that `_build.yml` contains all four active Android ABI targets with matching `--android_abi` values and `cd.yml` exposes all four dispatch presets.
- Local CMake configure checks for all four Android ABI targets with `ANDROID_SDK_ROOT=$HOME/Library/Android/sdk` and `ANDROID_NDK_HOME=$HOME/Library/Android/sdk/ndk/28.0.12433566`.
- Inspected generated ExternalProject configure commands for all four ABIs to verify `ANDROID_ABI`, `ANDROID_PLATFORM`, Android NDK toolchain, XNNPACK, and NNAPI flags.
- Representative Android zip manifest test with `onnxruntime/lib/libonnxruntime.a`, a public header, and a CMake dependency file for all four Android target names.
- `git diff --check`

## Issues Encountered

- Full Android ONNX Runtime compilation was not run locally in this loop because it would require expensive per-ABI native builds. Local validation covered argument plumbing, CMake generation, generated ExternalProject commands, archive shape, and manifest behavior.
- `gh` is not installed on this machine, so the Android workflow was not dispatched from the local loop. Follow-up command after installing/authenticating `gh`:

```bash
gh workflow run cd.yml --repo Kautenja/ort-artifacts --ref ralph-dev -f onnxruntime-ref=v1.22.2 -f target-preset=all -f target-custom=android -f buildtype=Release -f publish=false
```
