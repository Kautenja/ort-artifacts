# Specification: Checkbox Target Workflow Dispatch

Status: COMPLETE

## Feature: Manual Build Target Checkboxes

### Overview
Replace the manual CD workflow's target preset dropdown and free-form custom target filter with explicit GitHub Actions boolean inputs for build targets.

The current workflow dispatch form asks maintainers to choose a single preset or type a substring filter. That is powerful for maintainers who know the internal target names, but it is not friendly for people who just want to run one or more platform builds from the GitHub UI. The manual workflow should present clear checkboxes for the active build targets and convert those selections into the target list used by the reusable build workflow.

### User Stories
- As a release maintainer, I want to select build targets with checkboxes so that I can run platform-specific builds without memorizing target names.
- As a contributor, I want the manual workflow form to show the available build targets clearly so that I do not accidentally run every expensive platform build.
- As a maintainer, I want the selected targets to map deterministically to the existing artifact names so that release archives and manifests remain stable.

---

## Functional Requirements

### FR-1: Checkbox Inputs Replace Target Preset and Custom Filter
The manual CD workflow must remove the `target-preset` dropdown and `target-custom` string input from `workflow_dispatch`, replacing them with boolean inputs for target selection.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` no longer exposes `target-preset` in the manual workflow UI.
- [x] `.github/workflows/cd.yml` no longer exposes `target-custom` in the manual workflow UI.
- [x] The manual workflow exposes a `target-all` boolean input that runs every active matrix target when checked.
- [x] The manual workflow exposes boolean inputs for each active target currently present in `.github/workflows/_build.yml`.
- [x] Checkbox input descriptions use human-readable labels, such as `Linux x86_64 static`, while preserving stable internal target names in workflow logic.

### FR-2: Selected Targets Flow Into the Reusable Build Workflow
The reusable build workflow must receive a deterministic target selection derived from the checkbox inputs.

**Acceptance Criteria:**
- [x] `.github/workflows/_build.yml` accepts a target selection value that can represent one or more exact target names.
- [x] Matrix rows run only when their exact target name is selected, or when `target-all` is selected.
- [x] Substring matching is removed from the build decision path.
- [x] Selecting multiple target checkboxes in one manual workflow run builds all selected targets for the requested build type.
- [x] Existing matrix target names, build arguments, artifact names, archive names, and release manifest behavior remain unchanged.

### FR-3: Empty and Conflicting Selection Behavior
The workflow must handle common UI mistakes with clear behavior.

**Acceptance Criteria:**
- [x] If `target-all` is checked, all active targets build regardless of individual target checkbox values.
- [x] If `target-all` is unchecked and no individual target is checked, the workflow fails quickly before expensive setup or builds begin.
- [x] The failure message lists the expected action, for example: check `target-all` or select at least one target checkbox.
- [x] The validation step runs for both Debug and Release paths when `buildtype` is `Both`.

### FR-4: Active Target Coverage
The checkbox set must reflect the active targets in the reusable build matrix.

**Acceptance Criteria:**
- [x] The checkbox inputs include `linux-aarch64-static`.
- [x] The checkbox inputs include `linux-x86_64-static`.
- [x] The checkbox inputs include `macos-aarch64-static`.
- [x] The checkbox inputs include `macos-x86_64-static`.
- [x] The checkbox inputs include `windows-md-x86_64-static`.
- [x] The checkbox inputs include `ios-aarch64-static`.
- [x] The checkbox inputs include `ios-simulator-aarch64-static`.
- [x] The checkbox inputs include `ios-simulator-x86_64-static`.
- [x] The checkbox inputs include `android-arm64-v8a-static`.
- [x] The checkbox inputs include `android-armeabi-v7a-static`.
- [x] The checkbox inputs include `android-x86_64-static`.
- [x] The checkbox inputs include `android-x86-static`.
- [x] Disabled or commented-out matrix targets are not exposed as checkboxes unless they are re-enabled in the matrix as part of this work.

---

## Success Criteria

- A maintainer can open the GitHub manual CD workflow and choose build targets without using a dropdown of internal target names.
- A maintainer can run one target, multiple targets, or all targets from the GitHub UI.
- Accidental empty target selections fail before any platform setup or compilation starts.
- Existing release artifact naming and publishing behavior is unchanged for the same target set.

---

## Dependencies
- GitHub Actions `workflow_dispatch` boolean inputs.
- GitHub Actions support for up to 25 top-level manual workflow inputs.
- Existing reusable `_build.yml` matrix target names.
- Existing `buildtype`, `onnxruntime-ref`, and `publish` manual workflow inputs.

## Assumptions
- GitHub's current manual workflow input limit is sufficient for this repository: `onnxruntime-ref`, `buildtype`, `publish`, `target-all`, and one checkbox for each active build target.
- Checkboxes should select exact active targets, not broad platform groups, because platform groups would hide architecture and ABI differences.
- `target-all` should remain the fastest way to request the previous default behavior.
- Workflow dispatch input ordering in GitHub's UI will follow the YAML order closely enough to place target selection near the other build inputs.

## Implementation Notes

- Prefer keeping `_build.yml` as the single source of truth for actual target build arguments and runner choices.
- One implementation path is to have `cd.yml` assemble a comma-separated exact target list from checked inputs and pass it to `_build.yml`.
- Another acceptable implementation path is to pass the booleans through `workflow_call` inputs if the resulting YAML remains maintainable.
- Avoid adding a second workflow solely for checkbox dispatch unless the input limit or GitHub UI behavior makes the single-workflow approach impossible.
- Keep `buildtype` and `publish` behavior unchanged.
- Implemented `workflow_dispatch` target checkboxes named after the exact active matrix targets plus `target-all`.
- `cd.yml` assembles `all` or a comma-separated exact target list, and `_build.yml` validates that list before expanding a dynamic matrix.
- Empty selections fail in `_build.yml` before platform setup, and `Both` invokes that validation separately for Debug and Release.
- Target names, build arguments, artifact names, archive names, reduced-operator metadata, and publish flow remain unchanged for selected targets.

---

## Completion Signal

### Implementation Checklist
- [x] Replace `target-preset` and `target-custom` manual inputs with checkbox target inputs.
- [x] Add target selection validation before expensive setup/build steps.
- [x] Update `_build.yml` selection logic to use exact target membership rather than substring matching.
- [x] Verify all currently active matrix targets are represented by checkbox inputs.
- [x] Verify release artifact naming, archive naming, and manifest behavior remain unchanged.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] YAML syntax is valid.
- [x] Workflow expressions are valid for `workflow_dispatch` and `workflow_call`.
- [x] `./build.sh --dry-run` succeeds.
- [x] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py` succeeds.

#### Functional Verification
- [x] `target-all` selection includes every active matrix target.
- [x] A single checked target runs only that target's matrix row.
- [x] Multiple checked targets run only those target matrix rows.
- [x] Empty target selection fails before setup/build work.
- [x] `Debug`, `Release`, and `Both` build type paths pass the selected target list correctly.

#### Visual Verification (if UI)
- [x] GitHub manual workflow form exposes target selection as checkboxes, not the old preset dropdown and custom filter string.
- [x] Checkbox descriptions are readable by someone who does not know the internal target naming scheme.

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
