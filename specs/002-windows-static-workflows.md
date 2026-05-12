# Specification: Windows Static Artifact Workflows

Status: TODO

## Feature: Windows x86_64 Static ONNX Runtime Artifacts

### Overview
Enable GitHub Actions coverage for Windows x86_64 static ONNX Runtime artifacts so downstream native consumers can link prebuilt Windows libraries without maintaining their own ONNX Runtime build pipeline.

Windows x86_64 is required. Windows ARM64 is not required unless the implementation research finds a strong reason to include it now; the spec requires an explicit documented decision rather than silent omission.

### User Stories
- As a Windows native consumer, I want a static x86_64 ONNX Runtime artifact so that I can link it into a downstream C or C++ application.
- As a maintainer, I want Windows runtime linkage choices to be explicit so that consumers can choose the correct artifact for their CRT strategy.
- As a release maintainer, I want a recorded Windows ARM64 decision so that future work can revisit it without rediscovering the same facts.

---

## Functional Requirements

### FR-1: Windows x86_64 Matrix Targets
The reusable build workflow must include active Windows x86_64 static target coverage.

**Acceptance Criteria:**
- [ ] `.github/workflows/_build.yml` includes at least one active Windows x86_64 static matrix entry.
- [ ] The Windows target runs on a Windows GitHub-hosted runner.
- [ ] The Windows target uses the repository's `build.sh` entry point.
- [ ] The target name clearly communicates CRT linkage, such as `windows-md-x86_64-static` or `windows-mt-x86_64-static`.

### FR-2: CRT Linkage Strategy
The workflow must intentionally choose and document Windows dynamic CRT, static CRT, or both.

**Acceptance Criteria:**
- [ ] If both `windows-md-x86_64-static` and `windows-mt-x86_64-static` are enabled, both appear in workflow dispatch choices and artifact naming.
- [ ] If only one CRT strategy is enabled, the rationale is documented in project docs or completion log.
- [ ] The selected CRT mode passes the correct `build.sh` flags.
- [ ] Artifact names are unambiguous for downstream consumers.

### FR-3: Windows ARM64 Decision
The implementation must research whether Windows ARM64 static artifacts should be added now and record the outcome.

**Acceptance Criteria:**
- [ ] The final change documents one of these decisions: `defer Windows ARM64`, `add Windows ARM64`, or `blocked Windows ARM64`.
- [ ] If Windows ARM64 is added, the workflow uses a valid Visual Studio ARM64 configuration and distinct artifact names.
- [ ] If Windows ARM64 is deferred, the documentation states that x86_64 is the required target for this phase and ARM64 can become a later spec.
- [ ] The decision is reflected consistently in workflow targets and manual dispatch choices.

### FR-4: Windows Workflow Dispatch and Packaging
The manual CD workflow and packaging flow must support the selected Windows targets.

**Acceptance Criteria:**
- [ ] `.github/workflows/cd.yml` exposes selected Windows targets in `target-preset`.
- [ ] `target-custom` substring filtering can build only Windows targets.
- [ ] Each Windows build uploads exactly one zip archive named `ort-<onnxruntime-ref>-<windows-target>-<buildtype>.zip`.
- [ ] Draft release publishing includes Windows artifacts and `manifest.json`.

---

## Success Criteria

- A maintainer can run the CD workflow for the selected Windows x86_64 target and receive a usable static Windows zip artifact.
- Windows artifact names make architecture and CRT linkage clear.
- The repository contains a clear Windows ARM64 decision for this phase.
- Existing macOS and iOS workflow behavior is unchanged.

---

## Dependencies
- GitHub-hosted Windows runners.
- Visual Studio build tools available on the selected runner image.
- ONNX Runtime static Windows build support.
- Any Windows execution provider dependencies selected by the workflow.

## Assumptions
- Windows x86_64 is required.
- Windows ARM64 may be valuable later but is not automatically required for this phase.
- DirectML and XNNPACK remain desirable for Windows if the current patch set and dependency setup can support them.
- OpenVINO should only remain enabled for Windows if it can be installed and linked reliably in the selected runner configuration.

---

## Completion Signal

### Implementation Checklist
- [ ] Enable selected Windows x86_64 static target or targets in `.github/workflows/_build.yml`.
- [ ] Add selected Windows target choices to `.github/workflows/cd.yml`.
- [ ] Verify Visual Studio, Ninja, CRT, and execution provider setup.
- [ ] Record the Windows ARM64 decision.
- [ ] Verify artifact upload, naming, and manifest behavior.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] YAML syntax is valid.
- [ ] Windows shell snippets are valid for the selected runner shell.
- [ ] `./build.sh --dry-run --static --directml --xnnpack -N` succeeds for the selected dynamic CRT-style arguments if used.
- [ ] `./build.sh --dry-run --static --mt --directml --xnnpack -N` succeeds for the selected static CRT-style arguments if used.

#### Functional Verification
- [ ] All acceptance criteria verified.
- [ ] At least one GitHub Actions run validates each selected Windows x86_64 target, or the inability to run it is documented with the exact follow-up command.
- [ ] Windows ARM64 decision is documented.
- [ ] Any unavailable local platform validation is documented in `completion_log/`.

#### Visual Verification (if UI)
- [ ] Not applicable.

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

