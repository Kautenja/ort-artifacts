# Specification: Execution Provider Workflow Checkboxes
Status: COMPLETE

## Feature: Manual Execution Provider Toggles

### Overview
Add GitHub Actions manual workflow checkboxes for optional execution providers supported by this repository, while preserving the current per-target provider defaults.

Today execution provider choices are embedded in the target matrix arguments, such as Linux using XNNPACK and OpenVINO, Windows using XNNPACK and DirectML, Apple targets using XNNPACK and CoreML, and Android using XNNPACK and NNAPI. Maintainers should be able to disable or enable optional provider families from the manual workflow form without editing YAML or creating one-off target entries.

### User Stories
- As a release maintainer, I want to disable XNNPACK from a manual build so that I can isolate provider-related failures or compare artifact size.
- As a platform maintainer, I want provider checkboxes for NNAPI, DirectML, CoreML, OpenVINO, and XNNPACK so that provider selection is understandable from the GitHub UI.
- As a downstream integrator, I want artifact behavior to match current defaults unless I intentionally change provider checkboxes.

---

## Functional Requirements

### FR-1: Provider Checkbox Inputs
The manual CD workflow must expose boolean inputs for optional execution providers used or supported by the active build system.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` exposes an `enable-xnnpack` boolean input with default `true`.
- [x] `.github/workflows/cd.yml` exposes an `enable-openvino` boolean input with default `true`.
- [x] `.github/workflows/cd.yml` exposes an `enable-directml` boolean input with default `true`.
- [x] `.github/workflows/cd.yml` exposes an `enable-coreml` boolean input with default `true`.
- [x] `.github/workflows/cd.yml` exposes an `enable-nnapi` boolean input with default `true`.
- [x] If WebGPU remains supported by `build.sh`/CMake and is intentionally exposed, it must use an `enable-webgpu` boolean input with default `false` unless an active target currently enables it.
- [x] Input descriptions clearly state that providers are applied only to compatible targets.

### FR-2: Preserve Current Defaults
Default checkbox values must reproduce the current matrix behavior.

**Acceptance Criteria:**
- [x] With all provider inputs left at their defaults, Linux static targets still receive `--xnnpack --openvino`.
- [x] With all provider inputs left at their defaults, Windows static targets still receive `--xnnpack --directml`.
- [x] With all provider inputs left at their defaults, macOS and iOS targets still receive `--xnnpack --coreml`.
- [x] With all provider inputs left at their defaults, Android targets still receive `--xnnpack --nnapi`.
- [x] Providers not currently used by an active target are not added to that target merely because their global checkbox default is `true`.

### FR-3: Provider Selection Plumbing
The reusable build workflow must derive target-specific `build.sh` arguments from the selected provider checkboxes and platform compatibility rules.

**Acceptance Criteria:**
- [x] `.github/workflows/_build.yml` accepts provider-selection inputs from `cd.yml`.
- [x] Provider flags are appended to `build.sh` only when both the checkbox is enabled and the selected matrix target supports that provider.
- [x] Disabling `enable-xnnpack` removes `--xnnpack` from every selected target.
- [x] Disabling `enable-openvino` removes `--openvino` from Linux selected targets and skips OpenVINO setup steps.
- [x] Disabling `enable-directml` removes `--directml` from Windows selected targets.
- [x] Disabling `enable-coreml` removes `--coreml` from macOS and iOS selected targets.
- [x] Disabling `enable-nnapi` removes `--nnapi` from Android selected targets.
- [x] Provider setup steps, such as OpenVINO installation, run only when the resulting target arguments include the corresponding provider.

### FR-4: Compatibility and Validation
Provider toggles must not create invalid build combinations silently.

**Acceptance Criteria:**
- [x] DirectML is never passed to non-Windows targets.
- [x] CoreML is never passed to non-Apple targets.
- [x] NNAPI is never passed to non-Android targets.
- [x] OpenVINO is never passed to macOS, iOS, or Android targets.
- [x] If a user explicitly enables a provider that has no compatible selected target, the workflow logs a clear notice but does not fail.
- [x] If all optional providers are disabled, targets still build with baseline ONNX Runtime behavior where supported.

---

## Success Criteria

- Maintainers can run the same artifacts as today without changing any provider input.
- Maintainers can disable one provider family for a selected build without editing workflow YAML.
- Provider-related setup and dependencies are skipped when the provider is disabled.
- Invalid platform/provider combinations are impossible from the manual workflow UI.

---

## Dependencies
- Existing `build.sh` flags: `--xnnpack`, `--openvino`, `--directml`, `--coreml`, `--nnapi`, and optionally `--webgpu`.
- Existing `.github/workflows/cd.yml` manual dispatch flow.
- Existing `.github/workflows/_build.yml` target matrix.
- Existing platform compatibility checks in `CMakeLists.txt`.

## Assumptions
- XNNPACK remains enabled by default for every currently active target.
- OpenVINO remains enabled by default only for Linux targets.
- DirectML remains enabled by default only for Windows targets.
- CoreML remains enabled by default only for macOS, iOS, and iOS simulator targets.
- NNAPI remains enabled by default only for Android targets.
- WebGPU is not part of current active target defaults and should remain disabled by default if exposed.

## Implementation Notes

- Prefer separating base target arguments from provider arguments in `_build.yml` so provider checkboxes can modify behavior without duplicating matrix rows.
- Keep artifact target names unchanged for the initial implementation, unless a disabled provider would make the artifact name misleading enough to require a follow-up spec.
- Coordinate carefully with `specs/005-checkbox-target-workflow-dispatch.md` if both specs are implemented together, because both alter workflow dispatch inputs and `_build.yml` selection plumbing.

## Completion Notes

- WebGPU remains intentionally unexposed in the manual workflow because no active target currently enables or supports it. `build.sh` still keeps `--webgpu` for future explicit build paths.
- The reusable workflow preserves each target's current default argument string and filters provider flags out when checkboxes are disabled, which keeps current artifacts unchanged by default.

---

## Completion Signal

### Implementation Checklist
- [x] Add provider checkbox inputs to `.github/workflows/cd.yml`.
- [x] Add matching provider inputs to `.github/workflows/_build.yml`.
- [x] Refactor matrix arguments so provider flags are derived from checkbox inputs and compatibility rules.
- [x] Scope provider setup steps to the effective provider flags.
- [x] Document any provider that remains intentionally unsupported as a manual checkbox.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] YAML syntax is valid.
- [x] Workflow expressions are valid for `workflow_dispatch` and `workflow_call`.
- [x] `./build.sh --dry-run` succeeds.
- [x] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py` succeeds.

#### Functional Verification
- [x] Default provider inputs produce the same effective `build.sh` arguments as the current active matrix.
- [x] Disabling each provider removes only that provider's flag from compatible selected targets.
- [x] Incompatible provider/platform combinations are not emitted.
- [x] OpenVINO setup is skipped when `enable-openvino` is false.
- [x] Android, Apple, Windows, and Linux dry-run argument generation is verified.

#### Visual Verification (if UI)
- [x] GitHub manual workflow form exposes provider choices as checkboxes.
- [x] Provider checkbox labels are understandable without knowing `build.sh` flags.

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
