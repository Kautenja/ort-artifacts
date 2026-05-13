# Specification: Single Visible CD Workflow

Status: COMPLETE

## Feature: Collapse Internal Build and Publish Workflows Out of the Actions Sidebar

### Overview
Make GitHub Actions show one top-level workflow for this repository: `CD`.

GitHub currently shows `CD`, `Build`, and `Publish` in the Actions sidebar because `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml` are all workflow files with top-level workflow names. `Build` and `Publish` are implementation details for `CD`; they do not expose useful manual UI and make the Actions page harder to understand.

The build functionality is still necessary. The goal is to remove `Build` as a separate visible workflow, not to remove build jobs. Prefer folding the reusable `_build.yml` jobs into `cd.yml` so build, universal packaging, and XCFramework packaging remain visible inside a `CD` run. Likewise, after `specs/011-simplify-cd-workflow-dispatch-inputs.md` removes manual publishing from `cd.yml`, remove the standalone `Publish` workflow file from `.github/workflows`.

GitHub's workflow syntax documentation says workflow names are displayed under the Actions tab, and if `name` is omitted GitHub displays the workflow file path instead. Reusable workflows also must live directly in `.github/workflows`. Therefore, simply removing `name: Build` or prefixing the file with an underscore is not enough to hide it from the sidebar.

### User Stories
- As a maintainer, I want the Actions sidebar to show only `CD` so that there is one obvious place to run artifact builds.
- As a maintainer, I want build jobs to remain available inside the `CD` run graph so that I can still debug failed platform builds.
- As a contributor, I do not want to see empty internal reusable workflows that look runnable but have no useful UI.

---

## Functional Requirements

### FR-1: Confirm Build Is an Internal Implementation Detail
The implementation must verify whether `_build.yml` is used only by `cd.yml` before removing it as a workflow file.

**Acceptance Criteria:**
- [x] Repository search finds no local caller of `.github/workflows/_build.yml` other than `.github/workflows/cd.yml`.
- [x] Repository search finds no documentation that tells external users or other repositories to call `_build.yml` directly.
- [x] If an external or documented caller is discovered, the work is split before completion instead of silently breaking that contract.
- [x] The implementation records in history that `Build` is still required as job logic, but not required as a separate top-level workflow.

### FR-2: Inline Build Workflow Behavior Into CD
The reusable build workflow behavior must be preserved inside `.github/workflows/cd.yml`.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` no longer contains `uses: ./.github/workflows/_build.yml`.
- [x] `.github/workflows/_build.yml` is removed from `.github/workflows` or converted into a non-workflow helper outside `.github/workflows`.
- [x] No remaining file under `.github/workflows` has `name: Build`.
- [x] Target validation still runs before expensive platform setup or builds.
- [x] `Debug`, `Release`, and `Both` buildtype selections still produce the same build target sets as before.
- [x] Existing target resolver behavior for single targets, multiple targets, derived universal targets, and `apple-xcframework` is preserved.
- [x] Existing provider toggle behavior is preserved for XNNPACK, OpenVINO, DirectML, CoreML, and NNAPI.
- [x] Existing reduced-operator config validation, metadata, and artifact-name hashing are preserved.
- [x] Existing artifact names and archive contents are unchanged for equivalent inputs.
- [x] Existing universal Apple packaging and Apple XCFramework packaging remain ordered after their source artifacts.
- [x] Windows artifact slimming and validation still run before Windows archives are uploaded.

### FR-3: Remove Standalone Publish Workflow From the Sidebar
The standalone `Publish` workflow must disappear from the Actions sidebar once publishing has been removed or inlined.

**Acceptance Criteria:**
- [x] `specs/011-simplify-cd-workflow-dispatch-inputs.md` is complete first, or this spec incorporates its removal of the manual `publish` input and stale publish job references.
- [x] `.github/workflows/cd.yml` no longer contains `uses: ./.github/workflows/_publish.yml`.
- [x] `.github/workflows/_publish.yml` is removed from `.github/workflows` if no longer used.
- [x] No remaining file under `.github/workflows` has `name: Publish`.
- [x] If release publishing is intentionally reintroduced later, it is implemented inside `CD` or through a helper script/action that does not create a second visible workflow.
- [x] Manifest generation support in `.github/scripts/generate_manifest.py` is left intact.

### FR-4: Leave Only CD as a Workflow File
The workflows directory must contain only the workflow that maintainers should interact with.

**Acceptance Criteria:**
- [x] `.github/workflows` contains exactly one workflow YAML file: `cd.yml`.
- [x] `cd.yml` has `name: CD`.
- [x] No file under `.github/workflows` contains `workflow_call`.
- [x] No file under `.github/workflows` calls another local workflow with `uses: ./.github/workflows/`.
- [x] README and validation documentation no longer reference `.github/workflows/_build.yml` or `.github/workflows/_publish.yml` as workflow files to lint.
- [x] Existing historical specs, history entries, and completion logs may remain as historical records and do not need rewriting.

### FR-5: Preserve the CD User Experience
Consolidating workflows must make the Actions UI simpler without hiding build diagnostics.

**Acceptance Criteria:**
- [x] The Actions sidebar shows `CD` as the only repository workflow after the change is pushed.
- [x] Build and packaging jobs still appear as jobs within a `CD` workflow run.
- [x] Job names clearly identify target, ONNX Runtime ref, and build type where they did before.
- [x] A failed platform build is still attributable to the specific target and build type from the `CD` run page.
- [x] The manual `CD` workflow dispatch form still satisfies the input-limit requirements from `specs/011-simplify-cd-workflow-dispatch-inputs.md`.

---

## Success Criteria

- The repository has one visible GitHub Actions workflow: `CD`.
- Maintainers can start all manual artifact builds from `CD`.
- Existing build, packaging, artifact upload, and manifest behavior remain unchanged for equivalent inputs.
- Internal implementation details no longer appear as empty or confusing sidebar workflows.

---

## Dependencies
- `specs/011-simplify-cd-workflow-dispatch-inputs.md`, because it removes the manual publish input and stale publish job path.
- Existing `.github/workflows/cd.yml`.
- Existing `.github/workflows/_build.yml` build, universal packaging, and XCFramework packaging jobs.
- Existing `.github/workflows/_publish.yml`, if still present when this spec starts.
- Existing `.github/scripts/resolve_build_targets.py` and tests.
- Existing `.github/scripts/generate_manifest.py`.
- Official GitHub Actions workflow syntax behavior for workflow names and reusable workflow file placement.

## Assumptions
- No external repository depends on calling this repository's `_build.yml` reusable workflow directly.
- The repository values a simple Actions sidebar more than keeping `_build.yml` as a reusable workflow boundary.
- Workflow size growth in `cd.yml` is acceptable if the build logic remains readable and validated.
- Helper scripts and composite actions under `.github/actions` or `.github/scripts` do not create visible workflow sidebar entries and may be used to keep `cd.yml` maintainable.

## Non-Goals
- Do not remove build functionality.
- Do not remove build jobs from the `CD` run graph.
- Do not create a separate replacement workflow for publishing.
- Do not rewrite historical spec, history, or completion-log references to old workflow filenames.
- Do not change artifact naming, target names, build arguments, provider defaults, reduced-operator behavior, or release manifest schema except where required by `specs/011-simplify-cd-workflow-dispatch-inputs.md`.

## Implementation Notes

- Prefer generating one dynamic build matrix that includes both target and build type, rather than keeping separate reusable workflow calls for Debug and Release.
- The target resolver may be extended to output buildtype-expanded matrices for build, universal packaging, and XCFramework packaging.
- Use scripts or composite actions for repeated setup and artifact-name calculations if that keeps `cd.yml` readable without reintroducing visible workflows.
- Deleting only the top-level `name:` field is not sufficient because GitHub falls back to displaying the workflow file path.
- Moving a reusable workflow into a subdirectory under `.github/workflows` is not supported for reusable workflows.
- Update README validation commands from linting three workflow files to linting only the remaining workflow file.

---

## Completion Signal

### Implementation Checklist
- [x] Confirm `_build.yml` and `_publish.yml` have no required callers outside `cd.yml`.
- [x] Complete or incorporate `specs/011-simplify-cd-workflow-dispatch-inputs.md`.
- [x] Inline build validation, build, universal packaging, and XCFramework packaging into `cd.yml`.
- [x] Remove `_build.yml` from `.github/workflows`.
- [x] Remove `_publish.yml` from `.github/workflows` after publish usage is gone.
- [x] Update README and validation commands for the single workflow file.
- [x] Record history and completion log entries.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] YAML syntax is valid for `.github/workflows/cd.yml`.
- [x] `actionlint` succeeds for `.github/workflows/cd.yml`, if available.
- [x] `git diff --check` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/resolve_build_targets.py .github/scripts/validate_required_operators_config.py` succeeds.

#### Functional Verification
- [x] Target resolver tests pass.
- [x] Local workflow-file check confirms only `.github/workflows/cd.yml` remains.
- [x] Local grep check finds no `workflow_call` under `.github/workflows`.
- [x] Local grep check finds no local workflow calls using `uses: ./.github/workflows/`.
- [x] Local grep check finds no active `name: Build` or `name: Publish` under `.github/workflows`.
- [x] CD manual dispatch input count remains no greater than 25.
- [x] `Debug`, `Release`, and `Both` paths generate expected buildtype-expanded matrices.
- [x] Empty target selection fails before platform setup or build work.
- [x] Representative artifact-name calculations match the pre-consolidation names.
- [x] Universal Apple and Apple XCFramework packaging still wait for required source artifacts.

#### Visual Verification (if UI)
- [x] After push, the GitHub Actions sidebar shows `CD` and does not show `Build` or `Publish`.
- [x] A `CD` run page still shows target-specific build and packaging jobs.

#### Console/Network Check (if web)
- [x] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the workflow, scripts, tests, or documentation
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=1
