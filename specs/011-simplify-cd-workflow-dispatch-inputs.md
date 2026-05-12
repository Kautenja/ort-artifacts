# Specification: Simplify CD Workflow Dispatch Inputs

## Feature: Remove Redundant Manual CD Inputs

### Overview
Simplify `.github/workflows/cd.yml` so the manual GitHub Actions form stays under GitHub's `workflow_dispatch` input limit.

The current manual CD workflow defines 26 inputs, which exceeds GitHub's limit of 25 inputs for a `workflow_dispatch` event. Two inputs are redundant or too costly for the limited input budget:

- `publish`, displayed as "Publish as draft release on GitHub."
- `target-all`, displayed as "All active targets"

The workflow should remove both options. Instead of using a separate "all targets" checkbox, every individual target checkbox should default to `true`. A default manual run should therefore still request all active targets, while maintainers can uncheck targets to run a narrower build.

### User Stories
- As a release maintainer, I want the CD workflow dispatch form to load without GitHub input-limit errors so that I can start manual builds from the GitHub UI.
- As a release maintainer, I want all targets selected by default so that the common full-build path does not require a separate "all" checkbox.
- As a maintainer, I want draft release publishing removed from this crowded manual form so that target and build configuration inputs fit inside GitHub's limit.

---

## Functional Requirements

### FR-1: Remove Manual Draft Publish Input
The manual CD workflow must no longer expose draft-release publishing as a `workflow_dispatch` input.

**Acceptance Criteria:**
- [ ] `.github/workflows/cd.yml` has no top-level `workflow_dispatch` input named `publish`.
- [ ] The GitHub manual workflow form no longer shows the description `Publish as draft release on GitHub.`
- [ ] `.github/workflows/cd.yml` contains no references to `inputs.publish`.
- [ ] Manual CD runs do not publish draft GitHub releases by default after this input is removed.
- [ ] `_publish.yml` and manifest generation behavior are left unchanged unless a small compatibility edit is required by the removal from `cd.yml`.
- [ ] If manual draft publishing is still needed, it is deferred to a separate follow-up spec with its own smaller workflow form instead of re-adding an input to `cd.yml`.

### FR-2: Remove Manual All Targets Input
The manual CD workflow must remove the `target-all` checkbox and use individual target defaults instead.

**Acceptance Criteria:**
- [ ] `.github/workflows/cd.yml` has no top-level `workflow_dispatch` input named `target-all`.
- [ ] The GitHub manual workflow form no longer shows the description `All active targets`.
- [ ] The target selection job no longer reads `inputs['target-all']` or a `TARGET_ALL` environment variable.
- [ ] The target selection job builds the selected target list only from individual target checkbox inputs.
- [ ] The reusable `_build.yml` workflow may keep accepting `targets: all` for internal or future callers, but `cd.yml` no longer emits `targets=all` from the manual dispatch path.

### FR-3: Default All Targets Through Individual Checkboxes
Every target checkbox in the manual CD workflow must default to selected.

**Acceptance Criteria:**
- [ ] `linux-aarch64-static` defaults to `true`.
- [ ] `linux-x86_64-static` defaults to `true`.
- [ ] `macos-aarch64-static` defaults to `true`.
- [ ] `macos-x86_64-static` defaults to `true`.
- [ ] `macos-universal-static` defaults to `true`.
- [ ] `windows-md-x86_64-static` defaults to `true`.
- [ ] `ios-aarch64-static` defaults to `true`.
- [ ] `ios-simulator-aarch64-static` defaults to `true`.
- [ ] `ios-simulator-x86_64-static` defaults to `true`.
- [ ] `ios-simulator-universal-static` defaults to `true`.
- [ ] `apple-xcframework` defaults to `true`.
- [ ] `android-arm64-v8a-static` defaults to `true`.
- [ ] `android-armeabi-v7a-static` defaults to `true`.
- [ ] `android-x86_64-static` defaults to `true`.
- [ ] `android-x86-static` defaults to `true`.
- [ ] Leaving all target defaults unchanged produces the same build, universal-artifact, and XCFramework target set that `target-all=true` produced before this change.
- [ ] Unchecking one or more target inputs narrows the selected target list without changing artifact names for the remaining targets.
- [ ] If every target checkbox is unchecked, the workflow still fails before expensive setup or build work with a clear message.

### FR-4: Stay Under GitHub's Workflow Dispatch Input Limit
The updated manual CD workflow must fit inside GitHub's `workflow_dispatch` input limit.

**Acceptance Criteria:**
- [ ] `.github/workflows/cd.yml` defines no more than 25 inputs under `on.workflow_dispatch.inputs`.
- [ ] With the current target, build, reduced-operator, and provider options, the expected input count after this change is 24.
- [ ] No new manual dispatch inputs are introduced as part of this work.
- [ ] A local verification command prints the final input count and fails or is treated as failed if the count is greater than 25.

---

## Success Criteria

- GitHub accepts `.github/workflows/cd.yml` without the `you may only define up to 25 inputs for a workflow_dispatch event` error.
- The manual CD form no longer contains `Publish as draft release on GitHub.` or `All active targets`.
- A default manual CD dispatch still requests all current build, universal, and XCFramework targets.
- The manual CD dispatch form has room for the current target and provider checkboxes without exceeding 25 inputs.

---

## Dependencies
- Existing manual CD workflow in `.github/workflows/cd.yml`.
- Existing reusable build workflow in `.github/workflows/_build.yml`.
- Existing target resolver in `.github/scripts/resolve_build_targets.py`.
- Existing target resolver tests in `.github/scripts/test_resolve_build_targets.py`.
- GitHub Actions `workflow_dispatch` limit of 25 inputs.

## Assumptions
- Removing the manual draft publish input is preferable to dropping a target or provider checkbox.
- Draft release publishing should not happen implicitly merely because the old `publish` input was removed.
- A separate publishing workflow can be specified later if maintainers still need manual draft release creation from GitHub Actions.
- The current target set is the desired default full-build set.

## Implementation Notes

- Remove the `publish` input block from `.github/workflows/cd.yml`.
- Remove or disable the `publish` job in `.github/workflows/cd.yml` so there is no stale `inputs.publish` condition.
- Remove the `target-all` input block from `.github/workflows/cd.yml`.
- Change each individual target checkbox default in `.github/workflows/cd.yml` from `false` to `true`.
- Simplify the `select-targets` job by deleting the `TARGET_ALL` branch and always emitting a comma-separated explicit target list.
- Preserve the existing empty-selection failure behavior in `_build.yml` or the target resolver.
- Keep artifact naming, build arguments, reduced-operator behavior, provider toggles, universal artifact packaging, and XCFramework packaging unchanged.
- Suggested local input-count check:

```bash
awk 'BEGIN { n = 0 } /^      [A-Za-z0-9_-]+:$/ { n++ } END { print n; exit (n > 25) }' .github/workflows/cd.yml
```

---

## Completion Signal

### Implementation Checklist
- [ ] Remove the `publish` manual workflow input and stale `inputs.publish` usage.
- [ ] Remove the `target-all` manual workflow input and stale target-all selection logic.
- [ ] Default every individual target checkbox to `true`.
- [ ] Verify the default checkbox state selects all current active, universal, and XCFramework targets.
- [ ] Verify manual dispatch input count is 24 and no greater than 25.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] YAML syntax is valid.
- [ ] Workflow expressions are valid for `workflow_dispatch` and `workflow_call`.
- [ ] `actionlint` succeeds for changed workflow files, if available.
- [ ] `git diff --check` succeeds.

#### Functional Verification
- [ ] Local input-count check reports 24 inputs for `.github/workflows/cd.yml`.
- [ ] Target resolver tests pass.
- [ ] A default manual dispatch configuration resolves to all currently selectable targets.
- [ ] A single checked target still resolves to that target and any required derived-artifact prerequisites.
- [ ] An empty target selection still fails before platform setup or build work.
- [ ] Build, universal artifact, XCFramework, provider, and reduced-operator behavior remain unchanged for equivalent selected target sets.

#### Visual Verification (if UI)
- [ ] GitHub manual workflow form no longer shows `Publish as draft release on GitHub.`
- [ ] GitHub manual workflow form no longer shows `All active targets`.
- [ ] Every individual target checkbox is selected by default.

#### Console/Network Check (if web)
- [ ] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the workflow, scripts, or tests
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=0
