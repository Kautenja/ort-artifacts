# Specification: Android Static Artifact Workflows

Status: COMPLETE

## Feature: Android Multi-ABI Static ONNX Runtime Artifacts

### Overview
Enable GitHub Actions coverage for static Android ONNX Runtime artifacts across the four standard Android ABIs: `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.

The artifacts are intended for downstream native C/C++ integration through CMake and JNI. The workflow must produce native static artifacts only; it must not package ONNX Runtime Java bindings, `onnxruntime4j`, or an AAR.

### User Stories
- As an Android native library maintainer, I want static ONNX Runtime artifacts for all standard Android ABIs so that my C/C++ code can link them before JNI binding.
- As a downstream app builder, I want ABI-specific archives so that Gradle or CMake integration can select the correct native library for each Android device architecture.
- As a release maintainer, I want Android artifacts included in the same manifest and draft release flow as other platforms.

---

## Functional Requirements

### FR-1: Android ABI Matrix Targets
The reusable build workflow must include active Android static targets for all four standard ABIs.

**Acceptance Criteria:**
- [x] `.github/workflows/_build.yml` includes active matrix entries for `android-arm64-v8a-static`, `android-armeabi-v7a-static`, `android-x86_64-static`, and `android-x86-static`.
- [x] Each Android target passes `--android` and the correct `--android_abi` value to `build.sh`.
- [x] Architecture-related `build.sh` and CMake behavior supports all four ABIs, including 32-bit ARM and 32-bit x86.
- [x] Target names appear consistently in artifact names, archive names, and manual workflow filters.

### FR-2: Android NDK Setup
The workflow must configure Android SDK and NDK dependencies for every Android ABI target.

**Acceptance Criteria:**
- [x] Android SDK setup runs for every Android target.
- [x] NDK setup runs for every Android target.
- [x] `ANDROID_NDK_HOME` and `ANDROID_SDK_ROOT` are available to `build.sh`.
- [x] Android setup steps are scoped to Android targets and do not affect Linux, Windows, macOS, iOS, or WebAssembly targets.

### FR-3: Static Native Output Only
Android artifacts must be native static build outputs suitable for CMake/JNI integration, not Java-first packages.

**Acceptance Criteria:**
- [x] The workflow does not build or package `onnxruntime4j`.
- [x] The workflow does not produce an AAR as the primary deliverable.
- [x] Each Android archive contains static native libraries, headers, and dependency files needed by a downstream CMake project.
- [x] Documentation or completion notes state that JNI binding is expected to happen in the consuming project.

### FR-4: Android Workflow Dispatch and Release Metadata
The manual CD workflow and publishing flow must include Android targets.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` exposes all four Android targets in `target-preset`.
- [x] `target-custom` substring filtering can build all Android targets or one ABI-specific Android target.
- [x] Selecting `all` includes the Android ABI targets.
- [x] Draft release publishing includes Android artifacts and `manifest.json`.
- [x] The manifest includes Android archive names and SHA256 checksums.

---

## Success Criteria

- A maintainer can run the CD workflow for each Android ABI and receive a usable static native zip artifact.
- A maintainer can run the CD workflow with a target filter that builds all Android static targets.
- Android outputs are suitable for downstream CMake/JNI consumption without Java binding or AAR packaging.
- Existing macOS and iOS workflow behavior is unchanged.

---

## Dependencies
- GitHub-hosted Ubuntu runners.
- Android SDK and NDK setup actions.
- ONNX Runtime Android static build support for `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- Existing archive upload and publish workflow behavior.

## Assumptions
- Android artifacts should be static, matching the existing Apple artifact strategy and downstream native integration plan.
- The required ABI set is `arm64-v8a`, `armeabi-v7a`, `x86_64`, and `x86`.
- NNAPI and XNNPACK remain desirable for Android if the current patch set and dependency setup can support them.
- If ONNX Runtime no longer supports a requested 32-bit ABI for the selected reference, the agent should document the blocker and create a follow-up spec rather than silently dropping the ABI.

## Implementation Notes

- Enabled four Android native static targets: `android-arm64-v8a-static`, `android-armeabi-v7a-static`, `android-x86_64-static`, and `android-x86-static`.
- Android targets use XNNPACK and NNAPI, configure the Android SDK/NDK only for Android matrix rows, and pass ABI-specific `--android_abi` values through `build.sh`.
- `build.sh` and CMake now map Android ABIs to explicit internal architectures so 32-bit ARM and 32-bit x86 are supported intentionally.
- Android artifacts remain native static archives for downstream CMake/JNI consumers; Java bindings, `onnxruntime4j`, and AAR packaging are intentionally excluded.

---

## Completion Signal

### Implementation Checklist
- [x] Enable Android static targets for all four standard ABIs in `.github/workflows/_build.yml`.
- [x] Add all four Android target choices to `.github/workflows/cd.yml`.
- [x] Adjust `build.sh` architecture handling if required for 32-bit Android ABIs.
- [x] Verify native static output contents and exclude Java/AAR deliverables.
- [x] Verify artifact upload, naming, and manifest behavior.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] YAML syntax is valid.
- [x] Android workflow shell snippets are syntax checked where practical.
- [x] `./build.sh --dry-run --static --android --android_abi arm64-v8a --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_abi armeabi-v7a --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_abi x86_64 --xnnpack --nnapi -N` succeeds.
- [x] `./build.sh --dry-run --static --android --android_abi x86 --xnnpack --nnapi -N` succeeds.

#### Functional Verification
- [x] All acceptance criteria verified.
- [x] At least one GitHub Actions run or local equivalent validates every Android ABI target.
- [x] Native output is checked for static libraries and headers.
- [x] Any unavailable local platform validation is documented in `completion_log/`.

#### Visual Verification (if UI)
- [x] Not applicable.

#### Console/Network Check (if web)
- [x] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=1
