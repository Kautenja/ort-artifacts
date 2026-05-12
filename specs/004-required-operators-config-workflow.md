# Specification: Required Operators Config Workflow Input

Status: COMPLETE

## Feature: Model-Specific Reduced Operator Builds

### Overview
Allow maintainers to provide an ONNX Runtime `*.required_operators.config` or `*.required_operators_and_types.config` file when manually launching the GitHub Actions CD workflow, so the generated ONNX Runtime artifacts can be reduced to the operators required by a specific model or model set.

ONNX Runtime documents this as the `--include_ops_by_config` custom build path. ORT format conversion can generate a `required_operators.config` file, and type-aware conversion can generate a `required_operators_and_types.config` file that can be used with reduced operator type support.

GitHub `workflow_dispatch` does not provide a native file picker. This workflow must therefore accept a base64-encoded config payload through a workflow input, decode it into a temporary file inside each selected build job, validate it, and pass the file path into the build system.

### User Stories
- As a model maintainer, I want to launch a CD workflow with my model's required operators config so that the produced static ORT binaries include only the kernels my model needs.
- As an Android or native app integrator, I want artifact names and manifests to show when a binary was built from a reduced operator config so that I cannot accidentally consume a full-operator artifact or a custom artifact for the wrong model set.
- As a release maintainer, I want the workflow to avoid logging or publishing raw config contents by default because generated comments can contain private model paths.

---

## Functional Requirements

### FR-1: Manual Workflow Config Input
The CD workflow must expose an optional reduced-operator config input for manual runs.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` includes an optional string input named `required-operators-config-base64`.
- [x] The input description documents that callers should base64-encode the contents of a `*.required_operators.config` or `*.required_operators_and_types.config` file.
- [x] The input is forwarded to both Debug and Release reusable build workflow calls.
- [x] Leaving the input empty preserves current full-operator build behavior and artifact naming.
- [x] Documentation shows both GitHub UI paste usage and a `gh workflow run` example using a local config file.

### FR-2: Decode, Validate, and Protect Config Contents
The reusable build workflow must decode and validate the config before invoking `build.sh`.

**Acceptance Criteria:**
- [x] `.github/workflows/_build.yml` accepts `required-operators-config-base64` as an optional `workflow_call` input.
- [x] When provided, each selected build job decodes the payload to a file under `$RUNNER_TEMP`, not into the repository checkout.
- [x] Invalid base64 fails the job before the expensive build step.
- [x] The decoded file is validated with a small parser or script that accepts blank lines, comment lines beginning with `#`, and operator lines in the expected `domain;opset;operators` shape.
- [x] Validation supports standard reduced operator config lines and type-reduction JSON suffixes emitted by ONNX Runtime tooling.
- [x] The workflow does not print the raw decoded config contents to logs.
- [x] The workflow records only safe metadata such as byte count, parsed operator count, and SHA256 hash.

### FR-3: Build System Propagation
The local build entrypoint and CMake orchestration must propagate the decoded config into the ONNX Runtime build.

**Acceptance Criteria:**
- [x] `build.sh` accepts `--required-operators-config <path>` and validates that the file exists and is non-empty.
- [x] `build.sh --dry-run --static --required-operators-config <sample-file> -N` shows the config path in the generated CMake command without printing file contents.
- [x] `CMakeLists.txt` exposes a cache variable for the required operators config path.
- [x] When the config path is non-empty, the ONNX Runtime ExternalProject enables reduced operator registration for the selected config.
- [x] Implementation verifies the current ONNX Runtime `onnxruntime-ref` mechanism used by this repository; it must not merely add a CMake define if ONNX Runtime also requires its `reduce_op_kernels` generation step.
- [x] The generated ExternalProject command or equivalent local configure evidence shows the reduced-ops path is active.
- [x] Full builds with no config remain byte-for-byte equivalent in generated build arguments where practical.

### FR-4: Optional Reduced Type Support
The workflow must allow type-aware configs without forcing type reduction for configs that do not contain type data.

**Acceptance Criteria:**
- [x] `.github/workflows/cd.yml` includes an optional boolean input named `enable-reduced-operator-type-support`, defaulting to `false`.
- [x] The input is forwarded through `_build.yml` into `build.sh`.
- [x] `build.sh` exposes a matching `--enable-reduced-operator-type-support` flag.
- [x] If enabled without a required operators config, the build fails early with a clear error.
- [x] The reduced type support flag is used only during the ONNX Runtime operator reduction step, matching ONNX Runtime's supported build flow for the selected reference.

### FR-5: Artifact Names, Manifests, and Release Metadata
Custom reduced-operator artifacts must be distinguishable from full-operator artifacts.

**Acceptance Criteria:**
- [x] When a config is provided, artifact archive names and upload artifact names include a short stable marker derived from the config SHA256, such as `ops-<12-hex-chars>`.
- [x] Full-operator artifact names remain unchanged when no config is provided.
- [x] Published release assets do not overwrite full-operator assets for the same ONNX Runtime ref, target, and build type.
- [x] `manifest.json` records whether each artifact is reduced-ops and includes the config SHA256 when applicable.
- [x] The raw required operators config is not included in uploaded artifacts or release metadata unless a future explicit opt-in is added.
- [x] Completion notes document how to correlate a config file to an artifact using the SHA256 hash.

### FR-6: Documentation and Operator Config Examples
Project documentation must make the feature easy to use safely.

**Acceptance Criteria:**
- [x] `README.md` documents how to generate or locate `*.required_operators.config` from ORT model conversion.
- [x] `README.md` documents how to base64 encode the config on macOS/Linux and Windows PowerShell.
- [x] `README.md` includes a complete `gh workflow run cd.yml` example using `target-preset`, `target-custom`, `buildtype`, and the base64 config input.
- [x] Documentation notes GitHub's `workflow_dispatch` input payload limit of 65,535 characters and recommends checking in or splitting the config only if the generated payload exceeds GitHub limits.
- [x] Documentation explains that reduced operator builds are model-set-specific and should not be treated as general-purpose ORT artifacts.

---

## Success Criteria

- A maintainer can launch the CD workflow with a required operators config and receive reduced-operator artifacts for any selected target.
- The same workflow still produces current full-operator artifacts when no config is supplied.
- A downstream integrator can identify the required-operators config hash from the artifact name and manifest.
- Invalid, empty, or malformed config payloads fail before long-running builds begin.
- The workflow avoids leaking model paths from generated config comments into logs, artifacts, or release metadata.

---

## Dependencies
- GitHub Actions `workflow_dispatch` and reusable workflow inputs.
- ONNX Runtime custom build support for `--include_ops_by_config`.
- ONNX Runtime reduced operator config format.
- Existing `build.sh`, CMake `ExternalProject`, archive upload, publish, and manifest generation flow.

## References
- ONNX Runtime custom build docs: https://onnxruntime.ai/docs/build/custom.html
- ONNX Runtime ORT format model docs: https://onnxruntime.ai/docs/performance/model-optimizations/ort-format-models.html
- ONNX Runtime reduced operator config docs: https://onnxruntime.ai/docs/reference/operators/reduced-operator-config-file.html
- GitHub Actions `workflow_dispatch` input docs: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#onworkflow_dispatchinputs

## Assumptions
- Required operator configs are usually small enough to fit inside GitHub's 65,535-character `workflow_dispatch` input payload limit.
- The config contents are not secret, but generated comments may reveal local model paths and should not be echoed.
- The initial implementation should support the existing static/native artifact strategy and should not introduce AAR, Java binding, or `onnxruntime4j` packaging.
- If ONNX Runtime's reduced-operator implementation differs across supported `onnxruntime-ref` values, the implementation should validate against the default pinned release first and document any unsupported older releases.

---

## Completion Signal

### Implementation Checklist
- [x] Add workflow inputs for base64 required-operators config and optional reduced type support.
- [x] Add config decode and validation behavior in the reusable build workflow.
- [x] Add `build.sh` flags and CMake cache variables for reduced operator builds.
- [x] Implement the ONNX Runtime reduced-operator generation step needed by the current ExternalProject flow.
- [x] Add artifact naming and manifest metadata for reduced-operator artifacts.
- [x] Update README usage instructions and examples.
- [x] Add completion log and history entries after validation.

### Testing Requirements

The agent MUST complete ALL before outputting the magic phrase:

#### Code Quality
- [x] YAML syntax is valid.
- [x] Workflow shell snippets are syntax checked where practical.
- [x] `./build.sh --dry-run` succeeds with no config.
- [x] `./build.sh --dry-run --static --required-operators-config <sample-file> -N` succeeds and includes reduced-ops build arguments.
- [x] `./build.sh --dry-run --enable-reduced-operator-type-support` without a config fails with a clear error.
- [x] Any new parser/helper script has focused unit tests or command-line validation tests.
- [x] `python3 -m py_compile .github/scripts/generate_manifest.py` and any new Python helper scripts succeeds.

#### Functional Verification
- [x] All acceptance criteria verified.
- [x] A representative sample required operators config is decoded from base64 and validated locally.
- [x] Invalid base64 and malformed config cases fail before build invocation.
- [x] Generated ExternalProject commands or local configure output prove reduced-ops generation is active when a config is provided.
- [x] Representative artifact names include `ops-<hash>` only when a config is provided.
- [x] Manifest generation records reduced-ops metadata and config SHA256 for representative custom artifacts.
- [x] Existing full-operator artifact naming and manifest behavior are unchanged.
- [x] Any unavailable GitHub runner validation is documented in `completion_log/`.

#### Visual Verification (if UI)
- [x] Not applicable.

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
