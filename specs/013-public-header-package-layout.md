# Specification: Public Header Package Layout

Status: COMPLETE

## Feature: Root-Level ONNX Runtime Public Headers

### Overview
Static artifacts currently copy the upstream ONNX Runtime source header tree into `onnxruntime/include/onnxruntime`, exposing raw paths such as `core/session/*.h` and `core/providers/**/*.h`. The distributed artifacts should instead match the package layout used by ONNX Runtime client packages: public C/C++ session headers and the enabled provider factory headers should be installed at the root of `onnxruntime/include/onnxruntime/*.h`.

This matters most for iOS and Android because previous consumer projects expect the compact root-level header set, with CoreML or NNAPI provider factory headers included only when those providers are enabled.

### User Stories
- As an iOS native consumer, I want `onnxruntime/include/onnxruntime/coreml_provider_factory.h` and the public session headers at the include root so that my existing Xcode integration continues to compile.
- As an Android native consumer, I want `onnxruntime/include/onnxruntime/nnapi_provider_factory.h` and the public session headers at the include root so that my existing NDK integration does not depend on raw upstream source paths.
- As a release maintainer, I want CI to reject artifacts that accidentally contain the raw upstream header tree.

---

## Functional Requirements

### FR-1: Static Build Header Install
The static build install rules must install only the expected public ONNX Runtime headers at `onnxruntime/include/onnxruntime/*.h`.

**Acceptance Criteria:**
- [x] `src/static-build/CMakeLists.txt` no longer installs the entire `${ONNXRUNTIME_SOURCE_DIR}/include/onnxruntime` directory.
- [x] Public session headers are installed at `onnxruntime/include/onnxruntime/*.h`.
- [x] `cpu_provider_factory.h` is installed at `onnxruntime/include/onnxruntime/cpu_provider_factory.h`.
- [x] Enabled provider factory headers such as CoreML, NNAPI, DirectML, and OpenVINO are installed at the same root-level include path.
- [x] Raw source header directories such as `onnxruntime/include/onnxruntime/core` are not packaged for current static targets.

### FR-2: iOS and Android Exact Header Sets
iOS and Android artifacts must preserve the compact header sets used by existing consumers.

**Acceptance Criteria:**
- [x] CoreML-enabled iOS artifacts contain exactly `coreml_provider_factory.h`, `cpu_provider_factory.h`, `onnxruntime_c_api.h`, `onnxruntime_cxx_api.h`, `onnxruntime_cxx_inline.h`, `onnxruntime_float16.h`, `onnxruntime_lite_custom_op.h`, `onnxruntime_run_options_config_keys.h`, and `onnxruntime_session_options_config_keys.h` under `onnxruntime/include/onnxruntime`.
- [x] NNAPI-enabled Android artifacts contain exactly `cpu_provider_factory.h`, `nnapi_provider_factory.h`, `onnxruntime_c_api.h`, `onnxruntime_cxx_api.h`, `onnxruntime_cxx_inline.h`, `onnxruntime_float16.h`, `onnxruntime_lite_custom_op.h`, `onnxruntime_run_options_config_keys.h`, and `onnxruntime_session_options_config_keys.h` under `onnxruntime/include/onnxruntime`.
- [x] The validator fails if any iOS or Android artifact includes nested raw header directories under `onnxruntime/include/onnxruntime`.

### FR-3: Packaging Validation
Artifact packaging must validate the header layout before upload.

**Acceptance Criteria:**
- [x] A reusable validation script checks staged static artifacts for required root-level headers and rejects raw nested header directories.
- [x] The CD workflow runs the validation script after each static build and before creating the uploaded archive.
- [x] Unit tests cover valid iOS and Android layouts, missing provider headers, and accidental raw header directories.
- [x] Apple universal and XCFramework packaging tests use the same `onnxruntime/include/onnxruntime/*.h` source layout expected from real static artifacts.

---

## Success Criteria

- New iOS and Android static artifacts expose the same public header filenames as the previous working package layout.
- Current Linux, Windows, macOS, iOS, Android, universal Apple, and Apple XCFramework packaging paths continue to validate.
- CI fails before upload if raw upstream ONNX Runtime header directories are staged in an artifact.

---

## Dependencies
- Existing static build CMake wrapper in `src/static-build/CMakeLists.txt`.
- Existing CD workflow archive staging under `build/artifact`.
- Existing Apple universal and XCFramework package scripts.

## Assumptions
- Static inference artifacts do not need ONNX Runtime training headers.
- XNNPACK does not require an additional public provider factory header in the current target set.
- Provider-specific public headers should be installed only when the corresponding provider is enabled for the artifact.

## Implementation Notes

- Replaced the raw `${ONNXRUNTIME_SOURCE_DIR}/include/onnxruntime` directory install with an explicit root-level public header list in `src/static-build/CMakeLists.txt`.
- The static install step clears `include/onnxruntime` before installing the curated public headers, then removes unexpected root headers and nested `core`/`session` directories as a final cleanup.
- Added `.github/scripts/validate_public_headers.py` and wired it into the CD build job before archive creation.
- Updated Apple XCFramework tests so source artifacts use `onnxruntime/include/onnxruntime/*.h`, matching real static artifact layout.
- Documented the public header packaging rule in `README.md`.

---

## Completion Signal

### Implementation Checklist
- [x] Replace raw source header directory installation with explicit root-level public header installation.
- [x] Add reusable staged artifact header-layout validation.
- [x] Run header validation in the CD build job before archiving.
- [x] Update Apple packaging fixtures to reflect the real root-level package layout.
- [x] Update README, history, and completion log.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] `./build.sh --dry-run` succeeds.
- [x] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py .github/scripts/validate_public_headers.py` succeeds.
- [x] Workflow YAML parsing succeeds for changed workflow files.
- [x] `git diff --check` succeeds.

#### Functional Verification
- [x] Header validator tests pass.
- [x] Existing script unit tests pass or unsupported platform skips are documented.
- [x] iOS dry-run build arguments still include CoreML when enabled by target resolution.
- [x] Android dry-run build arguments still include NNAPI when enabled by target resolution.
- [x] The exact iOS and Android header lists are validated with representative staged artifacts.

#### Visual Verification (if UI)
- [x] Not applicable.

#### Console/Network Check (if web)
- [x] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code, workflow, packaging, or documentation
3. Run tests again
4. Verify all criteria
5. Commit and push if operating in Ralph Loop mode
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=1
