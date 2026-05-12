# Specification: Linux Static Artifact Workflows

Status: TODO

## Feature: Linux x86_64 and aarch64 Static ONNX Runtime Artifacts

### Overview
Enable GitHub Actions coverage for static Linux ONNX Runtime artifacts so downstream native consumers can fetch repeatable release archives for both mainstream server architecture families: x86_64 and aarch64.

The Linux workflow must produce static artifacts in the same release and manifest flow used by the existing Apple static builds. The implementation should preserve the current project model: CMake drives ONNX Runtime, patches live in `src/patches/`, and GitHub Actions uploads zipped `build/artifact` output.

### User Stories
- As a native Linux consumer, I want Release and Debug static archives for x86_64 so that I can link ONNX Runtime into a downstream C or C++ project without building ONNX Runtime myself.
- As an ARM Linux consumer, I want equivalent aarch64 static archives so that server, edge, and embedded Linux targets have the same artifact availability as x86_64.
- As a maintainer, I want Linux targets selectable from the manual CD workflow so that I can build only one Linux target, all Linux targets, or every platform.

---

## Functional Requirements

### FR-1: Linux Matrix Targets
The reusable build workflow must include active Linux static targets for x86_64 and aarch64.

**Acceptance Criteria:**
- [ ] `.github/workflows/_build.yml` includes active matrix entries named `linux-x86_64-static` and `linux-aarch64-static`.
- [ ] Both Linux targets run on an Ubuntu GitHub-hosted runner.
- [ ] Both Linux targets request static builds and include the intended Linux execution providers already supported by this repository.
- [ ] The target names appear consistently in artifact names, archive names, and manual workflow filters.

### FR-2: Linux Cross-Compilation Setup
The workflow must configure Linux aarch64 cross-compilation reliably without breaking x86_64 Linux or existing Apple targets.

**Acceptance Criteria:**
- [ ] The aarch64 Linux target installs or configures an appropriate aarch64 cross toolchain.
- [ ] The build passes the correct CMake toolchain, sysroot, compiler, and architecture flags for aarch64.
- [ ] The x86_64 Linux target uses the native Ubuntu runner toolchain without aarch64-only setup.
- [ ] Linux-specific environment variables are scoped to Linux targets and do not affect macOS, iOS, Windows, Android, or WebAssembly targets.

### FR-3: Linux Workflow Dispatch Options
The manual CD workflow must expose Linux targets as selectable presets.

**Acceptance Criteria:**
- [ ] `.github/workflows/cd.yml` includes `linux-x86_64-static` and `linux-aarch64-static` in the `target-preset` choices.
- [ ] `target-custom` substring filtering can still build either Linux target independently.
- [ ] Selecting `all` includes both Linux targets.
- [ ] Existing Apple target options continue to work.

### FR-4: Linux Artifact Packaging and Release Metadata
Linux artifacts must flow through upload, download, manifest generation, and draft release publishing without special manual steps.

**Acceptance Criteria:**
- [ ] Each Linux build uploads exactly one zip archive named `ort-<onnxruntime-ref>-<linux-target>-<buildtype>.zip`.
- [ ] Draft release publishing includes Linux artifacts and `manifest.json`.
- [ ] The manifest includes Linux archive names and SHA256 checksums.
- [ ] Linux archives contain the expected static library, headers, and dependency files required by downstream native linking.

---

## Success Criteria

- A maintainer can run the CD workflow for `linux-x86_64-static` and receive a usable static Linux x86_64 zip artifact.
- A maintainer can run the CD workflow for `linux-aarch64-static` and receive a usable static Linux aarch64 zip artifact.
- The `all` preset includes Linux, macOS, and iOS static targets.
- Existing macOS and iOS workflow behavior is unchanged.

---

## Dependencies
- GitHub-hosted Ubuntu runners.
- ONNX Runtime support for static Linux x86_64 and aarch64 builds.
- Any Linux execution provider dependencies selected by the workflow.
- Existing archive upload and publish workflow behavior.

## Assumptions
- Linux artifacts should be static, matching the existing Apple artifact strategy.
- Required Linux architectures are x86_64 and aarch64.
- OpenVINO and XNNPACK remain desirable for Linux if the current patch set and dependency setup can support them.
- If an execution provider prevents one Linux architecture from building, the agent should document the blocker and either fix it or narrow the provider set with a clear rationale in the completion log.

---

## Completion Signal

### Implementation Checklist
- [ ] Enable Linux x86_64 and aarch64 static targets in `.github/workflows/_build.yml`.
- [ ] Add Linux target choices to `.github/workflows/cd.yml`.
- [ ] Adjust Linux toolchain, OpenVINO, and CMake environment setup as needed.
- [ ] Verify artifact upload, naming, and manifest behavior.
- [ ] Update project documentation if new Linux build behavior or limitations need to be explained.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] YAML syntax is valid.
- [ ] Shell snippets in workflow steps are syntax checked where practical.
- [ ] `./build.sh --dry-run --static --xnnpack -N --openvino` succeeds for Linux x86_64 arguments.
- [ ] `./build.sh --dry-run --static -A aarch64 --xnnpack -N --openvino` succeeds for Linux aarch64 arguments.

#### Functional Verification
- [ ] All acceptance criteria verified.
- [ ] At least one GitHub Actions run or local equivalent validates Linux x86_64 configuration.
- [ ] At least one GitHub Actions run or local equivalent validates Linux aarch64 configuration.
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

