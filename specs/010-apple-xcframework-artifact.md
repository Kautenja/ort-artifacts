# Specification: Apple XCFramework Artifact

## Feature: Xcode-Ready ONNX Runtime XCFramework

### Overview
Create a platform-spanning ONNX Runtime XCFramework artifact for Apple consumers.

The desired package is equivalent to this manual workflow:

```bash
xcodebuild -create-xcframework \
  -library ort-rel-1.22.2-static-aarch64-ios/lib/libonnxruntime.a \
  -headers include \
  -library ort-rel-1.22.2-static-ios-simulator-universal/lib/libonnxruntime.a \
  -headers include \
  -library ort-rel-1.22.2-static-macos-universal/lib/libonnxruntime.a \
  -headers include \
  -output onnxruntime.xcframework
```

The repository should produce this from CI artifacts using the current package layout, headers, and artifact naming. iOS device and iOS simulator slices are known to work in the manual flow. The macOS slice previously failed in Xcode with missing system headers, so this spec must investigate and validate the macOS consumer path instead of merely creating a syntactically valid XCFramework.

This spec depends on `specs/009-apple-universal-static-artifacts.md`, which creates the `ios-simulator-universal-static` and `macos-universal-static` source artifacts.

### User Stories
- As an Xcode integrator, I want one `onnxruntime.xcframework` artifact that covers iOS devices, iOS simulators, and macOS so that I can drop it into an Xcode project.
- As a release maintainer, I want the XCFramework created from the same CI artifacts we publish separately so that the package is reproducible.
- As a macOS consumer, I want the macOS slice to compile and link in a minimal Xcode or clang smoke test so that missing SDK/system-header issues are caught before release.

---

## Functional Requirements

### FR-1: XCFramework Packaging
The workflow must create an Apple XCFramework from existing Apple static artifacts.

**Acceptance Criteria:**
- [ ] Create `onnxruntime.xcframework` with `xcodebuild -create-xcframework`.
- [ ] Include the iOS device arm64 library from `ios-aarch64-static`.
- [ ] Include the iOS simulator universal library from `ios-simulator-universal-static`.
- [ ] Include the macOS universal library from `macos-universal-static` only after the macOS consumer smoke test passes.
- [ ] Pass the correct public ONNX Runtime headers with every `-library` input.
- [ ] The output artifact name follows the existing release naming pattern, for example `ort-<onnxruntime-ref>-apple-xcframework-<buildtype>`.
- [ ] Reduced-operator builds preserve the existing `ops-<12-hex-chars>` artifact-name marker for the XCFramework output.

### FR-2: Header and Package Layout
The XCFramework must be directly consumable by Xcode.

**Acceptance Criteria:**
- [ ] The packaged artifact contains `onnxruntime.xcframework` at a predictable path.
- [ ] Headers inside the XCFramework are the public ONNX Runtime headers required to include `onnxruntime_c_api.h` and `onnxruntime_cxx_api.h`.
- [ ] Header sources from iOS device, iOS simulator universal, and macOS universal artifacts are compared or otherwise verified before choosing the packaged header tree.
- [ ] If additional module maps, umbrella headers, README notes, or linker setting documentation are needed for Xcode consumption, they are included in the artifact or README.
- [ ] The package does not require consumers to manually copy a separate `include` directory next to the XCFramework.

### FR-3: macOS Slice Investigation and Fix
The known macOS slice issue must be investigated as part of the XCFramework work.

**Acceptance Criteria:**
- [ ] Reproduce or disprove the previous macOS failure with a minimal local or CI consumer test.
- [ ] The investigation distinguishes between missing SDK/system include paths, missing Apple frameworks, bad packaged headers, incompatible deployment target, static-library content, and incorrect consumer build settings.
- [ ] If the macOS artifact requires additional system frameworks or libraries, document the exact Xcode linker settings and include them in README or packaged notes.
- [ ] If the macOS static slice itself is built incorrectly, fix the macOS build or split a narrower blocking spec before marking this spec complete.
- [ ] The final XCFramework must not silently include a macOS slice that fails the macOS consumer smoke test.

### FR-4: Workflow and Release Integration
XCFramework creation must fit the existing CD and publish model.

**Acceptance Criteria:**
- [ ] Add a manual workflow checkbox or equivalent documented trigger for the Apple XCFramework artifact.
- [ ] Selecting the XCFramework target schedules or requires `ios-aarch64-static`, `ios-simulator-universal-static`, and `macos-universal-static`.
- [ ] `target-all=true` includes the Apple XCFramework artifact after its source artifacts are produced.
- [ ] The publish workflow uploads the XCFramework artifact when `publish=true`.
- [ ] `.github/scripts/generate_manifest.py` records the XCFramework archive with a clear artifact type and SHA256.
- [ ] Existing static artifact publishing remains unchanged.

---

## Success Criteria

- A Release CD run can produce an `onnxruntime.xcframework` archive for iOS device, iOS simulator, and macOS.
- Xcode or clang can compile and link a minimal iOS simulator consumer against the XCFramework.
- Xcode or clang can compile and link a minimal macOS consumer against the XCFramework.
- The macOS missing-system-header concern is resolved, documented with exact consumer requirements, or split into a blocking follow-up before this spec is marked complete.
- The XCFramework artifact can be located through the release manifest and downloaded without manual reconstruction.

---

## Dependencies
- `specs/009-apple-universal-static-artifacts.md` must be complete.
- Existing `ios-aarch64-static` artifact.
- New `ios-simulator-universal-static` artifact.
- New `macos-universal-static` artifact.
- macOS runner support for `xcodebuild`, `xcrun`, `lipo`, and Apple SDK smoke tests.
- Existing manifest and publish workflows.

## Assumptions
- The iOS device arm64 static artifact remains single-architecture because iOS device builds only need arm64.
- The iOS simulator and macOS libraries should be universal before entering `xcodebuild -create-xcframework`.
- The same public ONNX Runtime header tree should work across iOS device, iOS simulator, and macOS for a given ONNX Runtime ref and build configuration.
- CoreML-enabled static builds may require Apple system frameworks at consumer link time.

## Non-Goals
- Do not create Android, Windows, Linux, or WebAssembly framework bundles.
- Do not remove or replace the raw static Apple artifacts.
- Do not hide a broken macOS slice by shipping an unvalidated three-platform XCFramework.
- Do not solve Swift package distribution unless it is the minimal way to make Xcode consumption reliable.

## Implementation Notes

- Prefer a reusable script, for example `scripts/create_apple_xcframework.sh`, that can run locally against unpacked artifacts and in GitHub Actions.
- The script should accept explicit paths for iOS device, iOS simulator universal, macOS universal, headers, and output directory instead of guessing from the current working directory.
- Add a small smoke-test fixture or generated temporary project that includes ONNX Runtime headers and references `OrtGetApiBase`.
- For macOS, compile and link using the macOS SDK discovered by `xcrun --sdk macosx --show-sdk-path`.
- For iOS simulator, compile and link using the simulator SDK discovered by `xcrun --sdk iphonesimulator --show-sdk-path`.
- If additional frameworks are required, prefer documenting them exactly rather than baking incomplete assumptions into the artifact.

---

## Completion Signal

### Implementation Checklist
- [ ] Ensure spec 009 universal Apple artifacts are available.
- [ ] Implement local and workflow XCFramework packaging.
- [ ] Add manual target selection support for the XCFramework artifact.
- [ ] Add macOS and iOS simulator consumer smoke tests.
- [ ] Investigate and fix or explicitly split the macOS slice issue.
- [ ] Update README and manifest support.
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
- [ ] `xcodebuild -create-xcframework` succeeds with the expected iOS device, iOS simulator universal, and macOS universal inputs.
- [ ] `xcodebuild -showdestinations` or equivalent SDK discovery confirms the runner has the required Apple SDKs.
- [ ] The generated XCFramework contains iOS device, iOS simulator, and macOS library identifiers.
- [ ] `lipo -info` verifies expected architectures inside the simulator and macOS libraries before packaging.
- [ ] A minimal iOS simulator consumer compile/link smoke test succeeds.
- [ ] A minimal macOS consumer compile/link smoke test succeeds, or the spec is split before completion because the macOS slice requires separate repair.
- [ ] Manifest generation succeeds against a representative XCFramework artifact archive.
- [ ] Existing raw static Apple artifacts still publish with unchanged names.

#### Visual Verification (if UI)
- [ ] Not applicable.

#### Console/Network Check (if web)
- [ ] Not applicable.

### Iteration Instructions

If ANY check fails:
1. Identify the specific issue
2. Fix the code, workflow, packaging, or documentation
3. Run tests again
4. Verify all criteria
5. Commit and push
6. Check again

**Only when ALL checks pass, output:** `<promise>DONE</promise>`

NR_OF_TRIES=0
