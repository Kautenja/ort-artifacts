# Specification: Android API 24 Static Artifacts

## Status: COMPLETE

## Feature: API 24 Compatible Static ONNX Runtime for Android

### Overview
Android static ONNX Runtime artifacts previously built with the repository default Android API level of 35. When those archives were linked into a downstream JNI library with `minSdk 24`, some ABIs failed because the archive exposed API-29-only ELF TLS references such as `__tls_get_addr`. The `x86` archive had a separate failure: an MLAS AVX assembly path was not position-independent and could not be linked into `libsensoryface.so`.

The fix keeps static ONNX Runtime delivery while restoring an Android API 24 artifact contract for ONNX Runtime `v1.22.0`. The local downstream backup's previously working shared package was recoverable only as ONNX Runtime `1.15.1`, not `v1.22.0`, so parity is documented as an API-24 behavior contract rather than proof that the historical shared artifact used the same ONNX Runtime reference. Android API 24 support was proven by rebuilding the static artifacts with API-24-compatible compiler/linker flags, validating each archive with a downstream shared-library link smoke test, and then testing the Android SDK with `minSdk 24`.

Android official NDK notes state that ELF TLS is available starting at API level 29, and that below API 29 the toolchain should use emulated TLS instead. Therefore an API 24 static artifact must not contain unresolved ELF TLS entry points such as `__tls_get_addr`; `__emutls_*` references are acceptable for pre-29 Android.

### User Stories
- As an Android SDK maintainer, I want static ONNX Runtime archives that link into a `minSdk 24` JNI library so that static delivery does not force Android 10 as the SDK floor.
- As a release maintainer, I want CI to reject Android static artifacts that contain API-29-only TLS or non-PIC objects so that consumers do not discover those failures inside their own Gradle builds.
- As a downstream app maintainer, I want the four standard Android ABIs preserved where technically feasible, with `x86` excluded only after the exact blocker is proven and documented.

---

## Functional Requirements

### FR-1: Android API 24 Artifact Contract
The Android static artifact build must target API 24 by default and by workflow target resolution.

**Acceptance Criteria:**
- [x] `build.sh` and `CMakeLists.txt` default Android builds to API 24 instead of API 35.
- [x] `.github/scripts/resolve_build_targets.py` passes `--android_api 24` for `android-arm64-v8a-static`, `android-armeabi-v7a-static`, `android-x86_64-static`, and `android-x86-static`.
- [x] The CD workflow still accepts the `onnxruntime-ref` input; `v1.22.0` is the primary validation reference for this spec.
- [x] `README.md` documents that Android static artifacts are built for API 24 and can be consumed by `minSdk 24` native Android libraries.

### FR-2: API-24-Compatible TLS and PIC Flags
Android static builds must compile ONNX Runtime and bundled dependencies in a way that is safe to link into downstream shared libraries targeting API 24.

**Acceptance Criteria:**
- [x] Android static builds set `CMAKE_POSITION_INDEPENDENT_CODE=ON` for all Android ABIs.
- [x] Android static builds disable LTO or otherwise prove that TLS lowering occurs during the artifact build, not later in the downstream SDK link.
- [x] For `ANDROID_API < 29`, Android static builds pass emulated TLS flags to C and C++ compilation so the archive does not contain `__tls_get_addr`.
- [x] Android assembly compilation receives PIC-compatible flags where supported.
- [x] Existing non-Android static, Apple, Windows, Linux, and WebAssembly behavior is unchanged.

### FR-3: Android x86 Static Link Compatibility
The `x86` static archive must either link cleanly into an API 24 shared library or be excluded only with a precise, documented reason.

**Acceptance Criteria:**
- [x] The implementation first attempts to preserve `android-x86-static`.
- [x] The known non-PIC object path or source, such as `SgemmKernelAvx.S.o`, is identified if `x86` still fails.
- [x] The preferred fix is narrowly scoped: force PIC for the offending x86 assembly path or disable only the non-PIC Android x86 MLAS assembly kernels while keeping generic kernels available.
- [x] `android-x86-static` remains enabled if the archive passes the API 24 link smoke test.
- [x] If `x86` cannot be made compatible with ONNX Runtime `v1.22.0`, the workflow may exclude `android-x86-static` only after the spec records the exact relocation, object file, attempted fixes, and downstream impact.

### FR-4: Static Archive Compatibility Validation
CI must validate Android static artifacts before upload so incompatible archives do not reach the SDK integration step.

**Acceptance Criteria:**
- [x] Add a reusable validation script for Android static artifacts, for example `.github/scripts/validate_android_static_archive.py`.
- [x] The validator rejects API 24 artifacts whose `libonnxruntime.a` exposes `__tls_get_addr` or ELF TLS relocations that require API 29.
- [x] The validator allows `__emutls_*` references for API levels below 29.
- [x] The validator performs a minimal NDK CMake link smoke test that builds a shared library against `onnxruntime::onnxruntime` with `ANDROID_PLATFORM=android-24`, `-Wl,--no-undefined`, and the artifact's ABI.
- [x] The CD build job runs the validator after public header validation and before archiving each Android static artifact.
- [x] Unit tests cover validator pass/fail behavior for TLS symbols, missing libraries, unsupported ABI names, and smoke-test command construction.

### FR-5: Downstream SDK Validation
The rebuilt artifacts must be proven in the Android SDK that triggered this work.

**Acceptance Criteria:**
- [x] Stage the rebuilt `v1.22.0` static artifacts under `SDK/sensoryface/src/main/jniLibs/<ABI>/include`, `lib`, and `lib/cmake/onnxruntime`.
- [x] Restore the Android SDK and demo to `minSdk 24` and remove the API 29-only workaround.
- [x] Enable `arm64-v8a`, `armeabi-v7a`, and `x86_64`; enable `x86` unless FR-3 documents a proven technical blocker.
- [x] `./main.sh release` passes.
- [x] `./main.sh test` passes, including connected tests on an API-compatible emulator or device.
- [x] Release and debug AARs contain `libsensoryface.so` for the validated ABIs and do not contain `libonnxruntime.so`.

### FR-6: Shared-Library Parity Report
The implementation must explain why the old shared-library package worked at API 24 while the first static package did not.

**Acceptance Criteria:**
- [x] Confirm the previous shared ONNX Runtime version, expected to be `v1.22.0`.
- [x] Record the previous shared package Android API level, NDK version, and recoverable compiler flags if available.
- [x] Compare the shared library and new static archive for TLS behavior, PIC behavior, and packaged ABI set.
- [x] Document whether the difference was caused by the static package being built at API 29+, missing emulated TLS flags, non-PIC x86 assembly, a version change, or a combination.

---

## Proposed Implementation Notes

- Pin Android static targets to `--android_api 24` in target resolution rather than relying only on shell defaults.
- In the Android branch of `CMakeLists.txt`, add Android static build arguments that enforce PIC and API-24 TLS behavior:
  - `CMAKE_POSITION_INDEPENDENT_CODE=ON`
  - `onnxruntime_ENABLE_LTO=OFF` and `CMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF` unless a tested LTO configuration preserves emulated TLS
  - `-fPIC` for C/C++ and assembly where applicable
  - `-femulated-tls` for C/C++ when `ANDROID_API` is less than 29
- If `x86` continues to emit `R_386_PC32` or equivalent non-PIC relocations from MLAS assembly, add a version-scoped ONNX Runtime patch under `src/patches/all-v1.22/` that removes only those Android x86 assembly sources from the static build. Prefer preserving the `x86` ABI with generic kernels over dropping the ABI.
- Use the NDK toolchain used by CD, currently `r28`, for archive validation. If `r28` cannot produce API 24 compatible output for `v1.22.0`, test the smallest NDK change before testing lower ONNX Runtime versions.
- Treat lower ONNX Runtime versions as a fallback only after `v1.22.0` has been rebuilt with API 24, PIC, no LTO, and emulated TLS settings.

---

## Success Criteria

- ONNX Runtime `v1.22.0` static artifacts can be consumed by the Android SDK at `minSdk 24`.
- `arm64-v8a`, `armeabi-v7a`, and `x86_64` are restored at API 24.
- `x86` is restored at API 24, or excluded with exact proof that `v1.22.0` static ONNX Runtime cannot provide a PIC-compatible archive for that ABI.
- No final AAR packages `libonnxruntime.so`.
- CI fails before upload if Android static archives regress to API-29-only TLS or non-PIC shared-library link failures.

---

## Dependencies
- Android NDK installed in CD through `nttld/setup-ndk@v1`, currently `r28`.
- ONNX Runtime source reference `v1.22.0`.
- Existing Android static build targets from `specs/003-android-static-workflows.md`.
- Existing public header validation from `specs/013-public-header-package-layout.md`.
- Downstream Android SDK at the path named by the investigation prompt, `/Users/ckauten/Documents/SensoryCloud/vision/face-sdk/sensory-face-android`, or the local equivalent if the checkout lives under a different home directory.

## Assumptions
- The SensoryFace native code needs only the ONNX Runtime C/C++ API already exposed by the current package.
- NNAPI and XNNPACK should remain enabled for Android unless they are proven to cause the API 24 incompatibility.
- `__emutls_*` references are acceptable for API 24 Android, while unresolved `__tls_get_addr` is not.
- The old shared-library package working at API 24 strongly suggests API 24 support is feasible for at least `arm64-v8a`, `armeabi-v7a`, and `x86_64` once the static archives are built with the correct Android floor.

---

## Completion Signal

### Implementation Checklist
- [x] Lower Android static artifact API target to 24 in build defaults and target resolution.
- [x] Add Android static PIC, no-LTO, and pre-29 emulated TLS build behavior.
- [x] Fix or document Android `x86` non-PIC MLAS assembly behavior.
- [x] Add Android static archive compatibility validation and unit tests.
- [x] Wire Android archive validation into CD before artifact upload.
- [x] Validate ONNX Runtime `v1.22.0` Android static artifacts for all required ABIs.
- [x] Validate the downstream Android SDK at `minSdk 24`.
- [x] Update README, history, and completion log.

### Completion Notes

- Validated ONNX Runtime `v1.22.0` Android static artifacts for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86` with Android API 24, NDK r28, public-header validation, archive TLS inspection, and the new NDK shared-library link smoke test.
- Kept `android-x86-static` enabled by excluding the Android x86 MLAS AVX assembly path and routing the Android x86 platform dispatch to SSE/generic kernels.
- Staged the rebuilt artifacts into the local downstream backup at `/tmp/sensory-face-android-api24.i1Essj` because the requested checkout path was not present. The temp SDK build restored `minSdk 24`, built release/debug AARs, packaged only `libsensoryface.so`, and passed `./main.sh test` through direct device instrumentation on `Medium_Phone_API_35` with `OK (157 tests)`.
- The local downstream backup's old shared ONNX Runtime package was `1.15.1` with `ORT_API_VERSION 15`; exact historical API level, NDK version, and compiler flags were not recoverable from this repository. The old shared library did not expose `__tls_get_addr`; the new `v1.22.0` static archives use `__emutls_*` where needed and do not expose `__tls_get_addr`.
- `gh` was not installed locally, so the Release CD workflow was not dispatchable from this machine. The CD-equivalent local Android target builds and validators were run against the same `build.sh`/CMake paths, and the workflow now runs the validator before Android static artifact upload.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] `./build.sh --dry-run` succeeds.
- [x] `./build.sh --dry-run --static --android --android_api 24 --android_abi arm64-v8a --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_api 24 --android_abi armeabi-v7a --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_api 24 --android_abi x86_64 --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_api 24 --android_abi x86 --xnnpack --nnapi -N` succeeds, unless `x86` is explicitly deferred by FR-3.
- [x] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py .github/scripts/validate_public_headers.py .github/scripts/validate_android_static_archive.py` succeeds.
- [x] Workflow YAML parsing succeeds for changed workflow files.
- [x] `git diff --check` succeeds.

#### Functional Verification
- [x] Android archive validator tests pass.
- [x] Existing script unit tests pass or unsupported platform skips are documented.
- [x] A Release CD run or CD-equivalent local run for `onnxruntime-ref=v1.22.0` builds `android-arm64-v8a-static`, `android-armeabi-v7a-static`, `android-x86_64-static`, and `android-x86-static`, unless `x86` is deferred by FR-3.
- [x] Each built Android artifact passes the API 24 NDK shared-library link smoke test.
- [x] Artifact inspection confirms no unresolved `__tls_get_addr` in API 24 Android static archives.
- [x] Artifact inspection confirms no non-PIC x86 relocation blocks downstream shared-library linking.
- [x] Public header validation still passes for Android artifacts.
- [x] The downstream Android SDK passes `./main.sh release` with `minSdk 24`.
- [x] The downstream Android SDK passes `./main.sh test` with `minSdk 24`.
- [x] AAR inspection confirms no packaged `libonnxruntime.so`.

#### Visual Verification (if UI)
- [x] Not applicable.

#### Console/Network Check (if web)
- [x] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific ABI, object file, relocation, symbol, or SDK command that failed
2. Fix the build flags, ONNX Runtime patch, archive validator, or downstream SDK integration
3. Run the targeted ABI validation again
4. Re-run the full required checks
5. Commit and push if operating in Ralph Loop mode
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=1
