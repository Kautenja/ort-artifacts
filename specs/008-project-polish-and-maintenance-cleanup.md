# Specification: Project Polish and Maintenance Cleanup

Status: COMPLETE

## Feature: README Refresh, Repository Cleanup, and Long-Term Maintainability Polish

### Overview
Make the repository feel clean, current, and trustworthy for the next maintainer session without changing build behavior.

The project has gained several workflow capabilities quickly: static targets across platforms, checkbox target selection, provider toggles, reduced-operator builds, patch guards, Ralph loop history, and completion logs. The README and repository surface now need a calm maintenance pass so a returning maintainer can understand the current workflow, avoid stale instructions, and distinguish source files from generated cruft.

This work is intentionally conservative. It should improve documentation, remove or ignore proven generated artifacts, and tighten organization only where the change is low risk and validated. It must not alter build outputs, target defaults, patch semantics, release metadata, or CI behavior except for documentation or housekeeping that is proven safe.

### User Stories
- As a returning maintainer, I want the README to describe the current workflows and targets accurately so that I can run a build without rediscovering recent changes.
- As a contributor, I want generated logs, prompt files, and one-off probe artifacts clearly ignored or removed so that the repository surface shows the code that matters.
- As a release maintainer, I want cleanup changes to be validated and documented so that polishing the repo does not accidentally change artifacts or break CI.
- As a future agent, I want clear maintenance notes and guardrails so that follow-up work starts from a tidy, reliable baseline.

---

## Functional Requirements

### FR-1: README Must Reflect Current Workflow State
Update `README.md` so it accurately describes the repository as it exists after specs 001-007.

**Acceptance Criteria:**
- [x] The README no longer references removed `target-preset` or `target-custom` manual workflow inputs.
- [x] The README explains manual target selection using the current target checkboxes, including the default `target-all` behavior.
- [x] The README documents provider checkboxes for XNNPACK, OpenVINO, DirectML, CoreML, and NNAPI, including that providers apply only to compatible targets.
- [x] The README retains and updates reduced-operator build instructions so examples use current workflow inputs.
- [x] The README gives a concise build target table or list with target name, platform, architecture, default providers, and important notes.
- [x] The README includes a short local validation section with the lightweight checks expected before committing.
- [x] The README explains the Ralph/spec workflow enough for a returning maintainer to know where specs, history, logs, and completion records live.

### FR-2: Repository Surface Cleanup
Identify generated, stale, duplicate, or one-off files that make the repository look messier than it is, then remove or ignore only items proven safe.

**Acceptance Criteria:**
- [x] A cleanup inventory is recorded in `history/` or `completion_log/` listing every candidate file or directory reviewed.
- [x] Root prompt artifacts such as `PROMPT_*.md` are classified as source, generated, or obsolete before any deletion.
- [x] Runtime logs under `logs/` are classified as intentionally retained history or generated cruft before any deletion.
- [x] One-off probe outputs such as `openvino_tbb_libs_*.txt` are classified as intentionally retained evidence or generated cruft before any deletion.
- [x] No file is removed unless `git ls-files`, `rg`, and surrounding docs/workflows show it is not required by build, release, validation, or project history.
- [x] If generated files should not be committed again, `.gitignore` is updated narrowly and documented.
- [x] Required placeholders such as `.gitkeep` files are preserved unless a directory is intentionally removed.

### FR-3: Documentation and Maintenance Notes
Improve maintainability without adding unnecessary process.

**Acceptance Criteria:**
- [x] Existing project principles in `.specify/memory/constitution.md` and `AGENTS.md` remain the source of truth and are not duplicated wholesale.
- [x] Any new maintenance guidance links to or summarizes the source of truth rather than creating conflicting rules.
- [x] Patch maintenance expectations are documented at a high level, including that ONNX Runtime patches must remain small, versioned, and validated with `git apply` checks.
- [x] The README or a small supporting doc explains how to validate GitHub Actions workflow YAML locally when workflow files change.
- [x] The cleanup leaves a clear path for future specs instead of hiding unfinished work.

### FR-4: Preserve Behavior and Artifact Contracts
The cleanup must not break existing build, workflow, or release behavior.

**Acceptance Criteria:**
- [x] No build target names change.
- [x] No default provider choices change.
- [x] No artifact naming, manifest schema, patch ordering, or release publishing behavior changes unless explicitly documented as a no-op cleanup.
- [x] No ONNX Runtime patch contents change except formatting fixes proven equivalent by `git apply` checks.
- [x] No workflow inputs are renamed, removed, or semantically changed as part of this polish pass.
- [x] Any code or workflow changes are limited to cleanup that can be verified locally without a live release.

---

## Success Criteria

- A returning maintainer can read the README and understand how to run the current manual CD workflow, target checkboxes, provider toggles, and reduced-operator builds.
- The repository root contains fewer unexplained generated or probe artifacts, or the remaining artifacts are clearly justified.
- Cleanup decisions are recorded so future agents do not rediscover the same files from scratch.
- Standard lightweight validation still passes after the cleanup.
- The diff is easy to review and does not mix cosmetic cleanup with behavior changes.

---

## Dependencies
- Current `README.md`.
- Current workflow inputs in `.github/workflows/cd.yml` and `.github/workflows/_build.yml`.
- Existing `.gitignore`, `history/`, `completion_log/`, `logs/`, and root generated/probe files.
- Existing Ralph loop instructions in `.specify/memory/constitution.md` and `AGENTS.md`.
- Existing patch directories under `src/patches/`.

## Assumptions
- Documentation polish is valuable even if no build code changes are needed.
- Some generated logs may have been intentionally committed as project history; they should not be removed without an explicit inventory and rationale.
- README examples should prefer current manual workflow inputs over older preset/custom examples.
- The active branch workflow is to work in the current branch unless the user explicitly requests a new branch or PR.
- A cleanup-only spec should bias toward leaving a questionable file in place with documentation rather than deleting it prematurely.

## Non-Goals
- Do not implement new platforms, providers, artifact formats, or build features.
- Do not slim Windows artifacts; that is covered by `specs/007-slim-windows-artifacts.md`.
- Do not rewrite the build system or Ralph loop scripts for style alone.
- Do not delete historical specs, completion logs, or history records merely to reduce file count.
- Do not create a new branch or PR unless explicitly directed by the user.

## Implementation Notes

- Start by comparing `README.md` against `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, `build.sh --help`, and recent specs/history.
- Use `git ls-files`, `rg`, and targeted file reads to classify cleanup candidates before deleting anything.
- Prefer narrow `.gitignore` entries for generated artifacts over broad patterns that might hide important build inputs.
- Keep the README practical and skimmable: target matrix, common commands, workflow inputs, validation, and maintenance notes should be easy to find.
- If a cleanup candidate is ambiguous, document it in the completion log and leave it for a future explicit spec.

---

## Completion Signal

### Implementation Checklist
- [x] Inventory README staleness and repository cleanup candidates.
- [x] Update `README.md` to reflect current target, provider, reduced-operator, and validation workflows.
- [x] Remove or ignore only proven generated/dead artifacts.
- [x] Preserve or document any ambiguous artifacts that should not be deleted yet.
- [x] Update history and completion log with cleanup decisions.
- [x] Verify no unintended behavior changes are present in the diff.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] `./build.sh --dry-run` succeeds.
- [x] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py` succeeds.
- [x] `git diff --check` succeeds.
- [x] If workflow files change, YAML parsing and `actionlint` succeed for changed workflows.

#### Functional Verification
- [x] README examples reference only current workflow inputs.
- [x] README target/provider documentation matches the active workflow matrix.
- [x] Every removed file has a documented reason and reference check.
- [x] `.gitignore` changes, if any, are narrow and do not hide required source inputs.
- [x] `git status --short` shows only intentional files before commit.

#### Visual Verification (if UI)
- [x] Not applicable.

#### Console/Network Check (if web)
- [x] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code or documentation
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=1
