# Specification: Apple Universal Static Artifacts

## Feature: Derived Universal macOS and iOS Simulator Static Archives

### Overview
Create and publish universal Apple static artifacts after the existing per-architecture Apple builds finish.

The current workflow builds separate `macos-aarch64-static`, `macos-x86_64-static`, `ios-simulator-aarch64-static`, and `ios-simulator-x86_64-static` artifacts. Downstream Xcode packaging often needs a single macOS universal static archive and a single iOS simulator universal static archive. These can be produced with `lipo` once both matching architecture slices have been compiled with the same ONNX Runtime ref, build type, providers, and reduced-operator configuration.

This spec intentionally stops at universal static archives. The final XCFramework package is covered by `specs/010-apple-xcframework-artifact.md`.

### User Stories
- As an Apple platform maintainer, I want macOS and iOS simulator universal static artifacts uploaded by CI so that I do not manually combine architecture-specific archives after every release.
- As an Xcode integrator, I want universal simulator and macOS libraries that preserve the existing headers and metadata so that they can be fed into `xcodebuild -create-xcframework`.
- As a release maintainer, I want universal artifacts to be deterministic derived outputs from already validated slices so that no extra source build path is introduced.

---

## Functional Requirements

### FR-1: Universal Apple Derived Targets
The CD workflow must be able to produce universal artifacts for macOS and iOS simulator.

**Acceptance Criteria:**
- [ ] Add support for an `ios-simulator-universal-static` derived artifact built from `ios-simulator-aarch64-static` and `ios-simulator-x86_64-static`.
- [ ] Add support for a `macos-universal-static` derived artifact built from `macos-aarch64-static` and `macos-x86_64-static`.
- [ ] The universal artifacts are produced with `lipo -create` from the two matching `libonnxruntime.a` inputs, not by recompiling ONNX Runtime a third time.
- [ ] The generated artifact names follow the existing release naming pattern, for example `ort-<onnxruntime-ref>-ios-simulator-universal-static-<buildtype>` and `ort-<onnxruntime-ref>-macos-universal-static-<buildtype>`.
- [ ] Reduced-operator builds preserve the existing `ops-<12-hex-chars>` artifact-name marker for universal outputs.

### FR-2: Target Selection and Dependency Resolution
Universal artifacts must integrate cleanly with the current checkbox target workflow.

**Acceptance Criteria:**
- [ ] Manual workflow inputs include clear checkboxes for `ios-simulator-universal-static` and `macos-universal-static`, or an equivalent documented mechanism that is visible in the CD workflow UI.
- [ ] `target-all=true` produces the universal Apple artifacts in addition to the existing architecture-specific Apple artifacts.
- [ ] Selecting a universal artifact explicitly schedules or requires the two source architecture builds needed to create it.
- [ ] If a universal artifact cannot be produced because a required source slice failed or was not selected, the workflow fails early with a clear error message instead of uploading a partial universal artifact.
- [ ] Selecting only an individual architecture target continues to build only that architecture unless the user also requests the universal derived artifact.

### FR-3: Artifact Contents and Metadata
Universal artifacts must look like normal ONNX Runtime artifacts except for the universal `libonnxruntime.a`.

**Acceptance Criteria:**
- [ ] The universal artifact contains the same top-level `onnxruntime` layout as existing Apple static artifacts.
- [ ] `onnxruntime/lib/libonnxruntime.a` is replaced by the universal library and contains both expected architectures according to `lipo -info`.
- [ ] Public headers are included exactly once and are taken from a validated matching source artifact.
- [ ] Header trees from the two source artifacts are compared or otherwise verified before one is chosen for the universal artifact.
- [ ] CMake/package metadata, if present, is preserved or deliberately adjusted so downstream consumers are not pointed at an architecture-specific library name or path.
- [ ] `reduced_operators.json`, if present, is preserved only when both source slices have matching reduced-operator metadata.

### FR-4: Manifest and Publishing Support
Publishing must treat universal artifacts as first-class release artifacts.

**Acceptance Criteria:**
- [ ] `.github/scripts/generate_manifest.py` recognizes the universal artifact archives and records correct SHA256, artifact name, library directory, and primary library path.
- [ ] The publish workflow uploads universal artifacts to draft releases when `publish=true`.
- [ ] Universal artifacts are not confused with the architecture-specific Apple artifacts in the manifest.
- [ ] Existing non-Apple artifacts and existing Apple architecture-specific artifacts retain their current names and behavior.

---

## Success Criteria

- A Release CD run can upload `ios-simulator-universal-static` with `libonnxruntime.a` containing `arm64` and `x86_64` simulator slices.
- A Release CD run can upload `macos-universal-static` with `libonnxruntime.a` containing `arm64` and `x86_64` macOS slices.
- Universal artifacts preserve headers, reduced-operator metadata, and package layout consistently with the source slices.
- Artifact names and manifest entries are predictable enough for the follow-up XCFramework spec to consume them without manual guessing.

---

## Dependencies
- Existing `macos-aarch64-static`, `macos-x86_64-static`, `ios-simulator-aarch64-static`, and `ios-simulator-x86_64-static` build targets.
- Existing CD target checkbox workflow in `.github/workflows/cd.yml`.
- Existing reusable build workflow in `.github/workflows/_build.yml`.
- Existing manifest generator in `.github/scripts/generate_manifest.py`.
- macOS runner support for `lipo`, `zip`, and artifact download/upload actions.

## Assumptions
- `lipo` can combine the current static archive outputs when both slices are built with the same ONNX Runtime ref, build type, provider toggles, and reduced-operator config.
- The iOS simulator aarch64 and x86_64 headers should be identical for a given ONNX Runtime ref and build configuration.
- The macOS aarch64 and x86_64 headers should be identical for a given ONNX Runtime ref and build configuration.
- The macOS universal artifact may still expose an underlying macOS consumer issue; final Xcode usability is validated in `specs/010-apple-xcframework-artifact.md`.

## Non-Goals
- Do not create an XCFramework in this spec.
- Do not change ONNX Runtime patch contents unless a patch is required to fix a source slice build failure and is validated separately.
- Do not remove existing architecture-specific Apple artifacts.
- Do not introduce new Apple deployment targets unless required to make the existing slices compatible and documented.

## Implementation Notes

- Prefer a small reusable script for combining source artifacts so local reproduction and workflow usage share the same behavior.
- Consider a workflow job that runs after matching Apple build jobs, downloads the source artifacts, verifies them, runs `lipo`, repackages the artifact, and uploads the derived archive.
- Keep universal artifact generation scoped to matching build types. Debug slices must combine only with Debug slices; Release slices must combine only with Release slices.
- If reduced-operator metadata exists, compare the metadata from both source slices before packaging the universal artifact.
- Record any macOS-specific warnings or link concerns in history, but leave the full Xcode consumer validation for spec 010.

---

## Completion Signal

### Implementation Checklist
- [ ] Add target selection support for macOS and iOS simulator universal derived artifacts.
- [ ] Implement universal artifact creation from existing per-architecture artifacts.
- [ ] Preserve or validate headers, metadata, and package layout.
- [ ] Update manifest generation and README documentation for universal artifacts.
- [ ] Record history and completion log entries.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] `./build.sh --dry-run` succeeds.
- [ ] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [ ] `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py` succeeds.
- [ ] Workflow YAML parsing succeeds for changed workflow files.
- [ ] `actionlint` succeeds for changed workflow files.
- [ ] `git diff --check` succeeds.

#### Functional Verification
- [ ] The target resolver behavior is tested for `target-all`, each universal target selected alone, both source architecture targets selected without the universal target, and invalid or missing prerequisite cases.
- [ ] A representative local or CI universal packaging run verifies `lipo -info` for `ios-simulator-universal-static`.
- [ ] A representative local or CI universal packaging run verifies `lipo -info` for `macos-universal-static`.
- [ ] Universal artifacts contain the expected `onnxruntime/lib/libonnxruntime.a` and headers.
- [ ] Manifest generation succeeds against representative universal artifact archives.
- [ ] Existing architecture-specific artifact names and manifest entries remain unchanged.

#### Visual Verification (if UI)
- [ ] Not applicable.

#### Console/Network Check (if web)
- [ ] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code or workflow
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=0
