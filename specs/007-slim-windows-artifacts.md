# Specification: Slim Windows Artifacts

## Feature: Investigate and Reduce Windows Artifact Size

### Overview
Investigate why the Windows static artifact is substantially larger than other platform artifacts and reduce its size where safe.

The current `windows-md-x86_64-static` artifact can be hundreds of megabytes larger than comparable targets. Some of that may be normal for a bundled MSVC static library with DirectML support, but debug symbols, provider runtime files, duplicate libraries, or unnecessary package metadata may be inflating the archive beyond what downstream consumers need.

### User Stories
- As a release maintainer, I want Windows artifact contents measured and explained so that I know which files are required and which are optional.
- As a downstream Windows integrator, I want the default archive to contain the files required to link and run, without unrelated or oversized extras.
- As a developer debugging Windows builds, I want symbols preserved in a deliberate place if they are removed from the main artifact.

---

## Functional Requirements

### FR-1: Artifact Size Inventory
The implementation must first measure and document the Windows artifact contents before removing files.

**Acceptance Criteria:**
- [ ] A Windows artifact content inventory lists each top-level directory and the largest files by compressed and uncompressed size where practical.
- [ ] The inventory identifies the size contribution of `onnxruntime/lib`, `onnxruntime/bin`, `.lib`, `.dll`, `.pdb`, and CMake/package metadata.
- [ ] The inventory distinguishes Release and Debug artifacts if both are available.
- [ ] The inventory is recorded in `history/` or `completion_log/` with enough detail to justify the slimming choices.

### FR-2: Required Runtime and Link Files
The implementation must classify files as required, optional, or removable for the current Windows target.

**Acceptance Criteria:**
- [ ] `onnxruntime/lib/onnxruntime.lib` or its configured equivalent is treated as required.
- [ ] Public headers required by downstream consumers are treated as required.
- [ ] CMake package files required for downstream CMake consumers are treated as required unless a documented replacement is provided.
- [ ] DirectML runtime DLLs required to use the DirectML execution provider are preserved when DirectML is enabled.
- [ ] Debug symbol files, especially `.pdb`, are evaluated separately from runtime/link requirements.

### FR-3: Reduce Main Windows Archive Size
The main Windows artifact must be slimmed without breaking expected downstream use.

**Acceptance Criteria:**
- [ ] Release Windows archives exclude unnecessary `.pdb` files from the main artifact unless the investigation proves they are required.
- [ ] If symbols are useful, they are either omitted intentionally with documentation or emitted as a separate symbol artifact.
- [ ] Unneeded duplicate provider/shared libraries are removed from the main archive if downstream static linking and runtime provider behavior still work.
- [ ] The Windows archive continues to include the files needed to link ONNX Runtime and run enabled dynamic provider components.
- [ ] The resulting Release Windows zip is meaningfully smaller than the measured baseline, or the completion notes explain why no safe reduction was possible.

### FR-4: Manifest and Publishing Behavior
Slimming must preserve release metadata correctness.

**Acceptance Criteria:**
- [ ] `.github/scripts/generate_manifest.py` still recognizes the slimmed Windows archive.
- [ ] Manifest entries still include the Windows archive name, SHA256, library directory, and primary ONNX Runtime library.
- [ ] If a separate symbol artifact is introduced, publishing behavior is documented and either included in release uploads or explicitly excluded.
- [ ] Existing non-Windows artifact behavior is unchanged.

---

## Success Criteria

- The Windows artifact size is explained with concrete file-level evidence.
- The Release Windows artifact no longer includes avoidable debug-symbol bulk in the main archive.
- DirectML-enabled Windows builds remain usable after slimming.
- Manifest generation and release publishing still work for Windows artifacts.

---

## Dependencies
- A successful Windows CI artifact, or an equivalent local Windows build, to inspect.
- Existing Windows target `windows-md-x86_64-static`.
- Existing DirectML install behavior in `src/static-build/CMakeLists.txt`.
- Existing archive and manifest flow in `.github/workflows/_build.yml` and `.github/scripts/generate_manifest.py`.

## Assumptions
- `DirectML.dll` is required for DirectML runtime support and should not be removed merely to reduce size.
- `.pdb` files are not required to link or run Release artifacts.
- Debug artifacts may remain larger than Release artifacts, but their contents should still be intentional.
- It is acceptable to produce a separate symbol artifact if it keeps debugging support available without bloating the default consumer package.

## Implementation Notes

- Start by downloading or inspecting a real Windows artifact rather than guessing from CMake alone.
- Prefer changing install/package rules over post-archive deletion if CMake can express the intended output cleanly.
- Consider separate handling for Release and Debug: Release should prioritize consumer size, while Debug may preserve more symbol information.
- Keep DirectML behavior coordinated with `specs/006-execution-provider-workflow-checkboxes.md` if provider toggles are implemented first.

---

## Completion Signal

### Implementation Checklist
- [ ] Obtain or create a representative Windows artifact for measurement.
- [ ] Record file-level size analysis for the baseline artifact.
- [ ] Decide which Windows files are required, optional, or removable.
- [ ] Implement safe archive slimming.
- [ ] Update documentation or completion notes to explain the Windows artifact contents.
- [ ] Verify manifest and release publishing behavior.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [ ] YAML syntax is valid if workflows change.
- [ ] CMake configure/generation succeeds for the Windows target or a documented local equivalent.
- [ ] `./build.sh --dry-run --static --directml --xnnpack -N` succeeds.
- [ ] `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh` succeeds.
- [ ] `python3 -m py_compile .github/scripts/generate_manifest.py` succeeds.

#### Functional Verification
- [ ] Baseline and slimmed Windows archive sizes are compared.
- [ ] Slimmed archive still contains the primary ONNX Runtime static library.
- [ ] Slimmed archive still contains required headers and CMake/package metadata.
- [ ] DirectML runtime files required for provider use are present when DirectML is enabled.
- [ ] Release archive `.pdb` handling is verified.
- [ ] Manifest generation succeeds against a representative slimmed Windows archive.

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
