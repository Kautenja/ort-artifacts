# Specification: Checkbox Target Workflow Dispatch

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
- [ ] `.github/workflows/cd.yml` no longer exposes `target-preset` in the manual workflow UI.
- [ ] `.github/workflows/cd.yml` no longer exposes `target-custom` in the manual workflow UI.
- [ ] The manual workflow exposes a `target-all` boolean input that runs every active matrix target when checked.
- [ ] The manual workflow exposes boolean inputs for each active target currently present in `.github/workflows/_build.yml`.
- [ ] Checkbox input descriptions use human-readable labels, such as `Linux x86_64 static`, while preserving stable internal target names in workflow logic.

### FR-2: Selected Targets Flow Into the Reusable Build Workflow
The reusable build workflow must receive a deterministic target selection derived from the checkbox inputs.

**Acceptance Criteria:**
- [ ] `.github/workflows/_build.yml` accepts a target selection value that can represent one or more exact target names.
- [ ] Matrix rows run only when their exact target name is selected, or when `target-all` is selected.
- [ ] Substring matching is removed from the build decision path.
- [ ] Selecting multiple target checkboxes in one manual workflow run builds all selected targets for the requested build type.
- [ ] Existing matrix target names, build arguments, artifact names, archive names, and release manifest behavior remain unchanged.

### FR-3: Empty and Conflicting Selection Behavior
The workflow must handle common UI mistakes with clear behavior.

**Acceptance Criteria:**
- [ ] If `target-all` is checked, all active targets build regardless of individual target checkbox values.
- [ ] If `target-all` is unchecked and no individual target is checked, the workflow fails quickly before expensive setup or builds begin.
- [ ] The failure message lists the expected action, for example: check `target-all` or select at least one target checkbox.
- [ ] The validation step runs for both Debug and Release paths when `buildtype` is `Both`.

### FR-4: Active Target Coverage
The checkbox set must reflect the active targets in the reusable build matrix.

**Acceptance Criteria:**
- [ ] The checkbox inputs include `linux-aarch64-static`.
- [ ] The checkbox inputs include `linux-x86_64-static`.
- [ ] The checkbox inputs include `macos-aarch64-static`.
- [ ] The checkbox inputs include `macos-x86_64-static`.
- [ ] The checkbox inputs include `windows-md-x86_64-static`.
- [ ] The checkbox inputs include `ios-aarch64-static`.
- [ ] The checkbox inputs include `ios-simulator-aarch64-static`.
- [ ] The checkbox inputs include `ios-simulator-x86_64-static`.
- [ ] The checkbox inputs include `android-arm64-v8a-static`.
- [ ] The checkbox inputs include `android-armeabi-v7a-static`.
- [ ] The checkbox inputs include `android-x86_64-static`.
- [ ] The checkbox inputs include `android-x86-static`.
- [ ] Disabled or commented-out matrix targets are not exposed as checkboxes unless they are re-enabled in the matrix as part of this work.

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

---

## Completion Signal

### Implementation Checklist
- [ ] Replace `target-preset` and `target-custom` manual inputs with checkbox target inputs.
- [ ] Add target selection validation before expensive setup/build steps.
- [ ] Update `_build.yml` selection logic to use exact target membership rather than substring matching.
- [ ] Verify all currently active matrix targets are represented by checkbox inputs.
- [ ] Verify release artifact naming, archive naming, and manifest behavior remain unchanged.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] YAML syntax is valid.
- [ ] Workflow expressions are valid for `workflow_dispatch` and `workflow_call`.
- [ ] `./build.sh --dry-run` succeeds.
- [ ] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [ ] `python3 -m py_compile .github/scripts/generate_manifest.py` succeeds.

#### Functional Verification
- [ ] `target-all` selection includes every active matrix target.
- [ ] A single checked target runs only that target's matrix row.
- [ ] Multiple checked targets run only those target matrix rows.
- [ ] Empty target selection fails before setup/build work.
- [ ] `Debug`, `Release`, and `Both` build type paths pass the selected target list correctly.

#### Visual Verification (if UI)
- [ ] GitHub manual workflow form exposes target selection as checkboxes, not the old preset dropdown and custom filter string.
- [ ] Checkbox descriptions are readable by someone who does not know the internal target naming scheme.

#### Console/Network Check (if web)
- [ ] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=0
