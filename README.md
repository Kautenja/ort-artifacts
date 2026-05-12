# ONNX Runtime Artifacts

Reproducible [ONNX Runtime](https://github.com/microsoft/onnxruntime) static artifacts for selected desktop, mobile, and Linux targets. CMake fetches ONNX Runtime, applies the patch set in `src/patches/`, and packages `build/artifact` output through GitHub Actions.

## Manual CD Workflow

Open **Actions > CD > Run workflow** to build artifacts on GitHub-hosted runners.

Important inputs:

- `onnxruntime-ref`: ONNX Runtime branch or tag. The current default is `v1.22.2`.
- `target-all`: builds every active target when checked. It defaults to `true` and preserves the normal full-matrix behavior.
- Target checkboxes: uncheck `target-all`, then check one or more exact target names such as `linux-x86_64-static`, `ios-simulator-aarch64-static`, `ios-simulator-universal-static`, or `apple-xcframework`. If `target-all` is false and no target checkbox is selected, the workflow fails before runner setup.
- Universal Apple checkboxes: `macos-universal-static` and `ios-simulator-universal-static` are derived with `lipo` after their matching aarch64 and x86_64 source slices finish. Selecting one schedules the required source slice builds; selecting only a source slice does not package a universal artifact.
- Apple XCFramework checkbox: `apple-xcframework` is derived from `ios-aarch64-static`, `ios-simulator-universal-static`, and `macos-universal-static`. Selecting it schedules the required source static and universal artifacts, validates headers and SDKs, runs macOS and iOS simulator consumer compile/link smoke tests, then uploads `ort-<onnxruntime-ref>-apple-xcframework-<buildtype>`.
- `buildtype`: `Release`, `Debug`, or `Both`.
- Provider checkboxes: `enable-xnnpack`, `enable-openvino`, `enable-directml`, `enable-coreml`, and `enable-nnapi` default to `true`. Each provider is added only to compatible selected targets; unsupported combinations are ignored with a workflow notice.
- `publish`: when true, successful artifacts are gathered by the publish workflow and uploaded to a draft release with `manifest.json`.

CLI example for one target:

```bash
gh workflow run cd.yml \
  -f onnxruntime-ref=v1.22.2 \
  -f target-all=false \
  -f linux-x86_64-static=true \
  -f buildtype=Release \
  -f publish=false
```

## Build Targets

Default providers below assume the provider checkboxes are left enabled.

| Target | Platform | Architecture | Default providers | Notes |
| --- | --- | --- | --- | --- |
| `linux-x86_64-static` | Linux | x86_64 | XNNPACK, OpenVINO | Native Ubuntu build. |
| `linux-aarch64-static` | Linux | aarch64 | XNNPACK, OpenVINO | Ubuntu-hosted cross build with GCC 11 ARM toolchain. |
| `macos-x86_64-static` | macOS | x86_64 | XNNPACK, CoreML | macOS 13.3 deployment target. |
| `macos-aarch64-static` | macOS | arm64 | XNNPACK, CoreML | macOS 13.3 deployment target. |
| `macos-universal-static` | macOS | arm64, x86_64 | XNNPACK, CoreML | Derived with `lipo` from the two macOS static slices. |
| `ios-aarch64-static` | iOS device | arm64 | XNNPACK, CoreML | iOS 15.0 deployment target. |
| `ios-simulator-aarch64-static` | iOS simulator | arm64 | XNNPACK, CoreML | Simulator build on macOS runner. |
| `ios-simulator-x86_64-static` | iOS simulator | x86_64 | XNNPACK, CoreML | Simulator build on macOS runner. |
| `ios-simulator-universal-static` | iOS simulator | arm64, x86_64 | XNNPACK, CoreML | Derived with `lipo` from the two simulator static slices. |
| `apple-xcframework` | iOS, iOS simulator, macOS | arm64, x86_64 where applicable | XNNPACK, CoreML | Derived with `xcodebuild -create-xcframework` from iOS device, simulator universal, and macOS universal static artifacts. |
| `windows-md-x86_64-static` | Windows | x64 | DirectML, XNNPACK | Static ORT libraries with the dynamic MSVC runtime (`/MD`). |
| `android-arm64-v8a-static` | Android | arm64-v8a | XNNPACK, NNAPI | Native static archive for downstream CMake/JNI integration. |
| `android-armeabi-v7a-static` | Android | armeabi-v7a | XNNPACK, NNAPI | Native static archive; no Java bindings or AAR are packaged. |
| `android-x86_64-static` | Android | x86_64 | XNNPACK, NNAPI | Native static archive for emulator or device integration. |
| `android-x86-static` | Android | x86 | XNNPACK, NNAPI | Native static archive for emulator integration. |

Windows static artifacts currently enable only the dynamic CRT target. Static CRT and Windows ARM64 variants are deferred to separate specs so runner, toolchain, and downstream-linking behavior can be validated independently.

Android artifacts are native static archives for consuming projects. They do not package ONNX Runtime Java bindings, `onnxruntime4j`, or an AAR.

Universal Apple artifacts preserve the normal `onnxruntime` package layout and replace only the primary static archive under `onnxruntime/lib`. The packaging step compares header trees and reduced-operator metadata before choosing one source artifact as the layout template. Reduced-operator universal artifacts keep the same `ops-<12-hex-chars>` marker as their source slices.

Apple XCFramework artifacts contain `onnxruntime.xcframework` and a packaged `README.md` at the archive root; consumers do not need to copy a separate `include` directory. The XCFramework packager compares public headers from the iOS device, iOS simulator universal, and macOS universal artifacts before choosing the packaged header tree. It verifies `lipo -info`, discovers Apple SDKs with `xcrun`, creates the bundle with `xcodebuild -create-xcframework`, and compiles/links minimal macOS and iOS simulator consumers before upload. For default CoreML-enabled Apple builds, Xcode consumers should link `Foundation.framework`, `CoreML.framework`, `Accelerate.framework`, and add `-lc++` to Other Linker Flags. The repository builds Apple artifacts with deployment targets iOS 15.0 and macOS 13.3.

## Ralph Wiggum Workflow

This repository is configured for the Ralph Wiggum autonomous spec loop. `AGENTS.md` points agents to `.specify/memory/constitution.md`, which is the source of truth for project principles, priority rules, validation expectations, autonomy, history, and completion signals.

Work items live in numbered specs under `specs/`; lower numbers have higher priority unless a user explicitly selects a spec. Ralph loop attempts are tracked with `NR_OF_TRIES` in each spec. Completed work is recorded in three places:

- `history.md`: one-line summaries.
- `history/YYYY-MM-DD--spec-name.md`: decisions, lessons, validation, and issues.
- `completion_log/YYYY-MM-DD--HH-MM-SS--spec-name.md`: completion summary, validation, and commit.

Run the Codex loop with:

```bash
./scripts/ralph-loop-codex.sh
```

Useful variants:

```bash
./scripts/ralph-loop-codex.sh plan
./scripts/ralph-loop-codex.sh 20
```

The loop writes generated prompt files at the repository root and runtime logs under `logs/`; those are ignored by git, while `logs/.gitkeep` preserves the directory.

## Reduced Operator Builds

Manual CD runs can build model-set-specific ONNX Runtime artifacts from a reduced operator config. Generate a config from ONNX Runtime tooling, for example with `create_reduced_build_config.py`, or keep the `required_operators.config` / `required_operators_and_types.config` emitted when converting ONNX models to ORT format. Type-aware configs can be used with `enable-reduced-operator-type-support`.

The workflow input expects the base64-encoded contents of the config file, not a path to the file. Use the config file emitted by ONNX Runtime tooling:

- `required_operators.config`: operator-only reduced build config.
- `required_operators_and_types.config`: type-aware reduced build config. Use this with `enable-reduced-operator-type-support=true`.

Base64 encode the file before starting the workflow. The raw config is decoded only under the runner temp directory and is not uploaded.

macOS/Linux:

```bash
CONFIG=required_operators.config
base64 < "$CONFIG" | tr -d '\n'
```

For a type-aware config, point `CONFIG` at the type-aware file:

```bash
CONFIG=required_operators_and_types.config
base64 < "$CONFIG" | tr -d '\n'
```

Windows PowerShell:

```powershell
$Config = "required_operators.config"
[Convert]::ToBase64String([IO.File]::ReadAllBytes($Config))
```

In the GitHub Actions UI, choose **CD**, select **Run workflow**, paste the single-line output into `required-operators-config-base64`, and enable `enable-reduced-operator-type-support` only for a type-aware config. Leave `target-all` checked for the full matrix, or uncheck it and select exact target checkboxes for a smaller run.

CLI example:

```bash
gh workflow run cd.yml \
  -f onnxruntime-ref=v1.22.2 \
  -f target-all=false \
  -f linux-x86_64-static=true \
  -f buildtype=Release \
  -f required-operators-config-base64="$(base64 < required_operators.config | tr -d '\n')" \
  -f enable-reduced-operator-type-support=false \
  -f publish=false
```

GitHub `workflow_dispatch` inputs are limited to 65,535 characters. If the generated base64 payload is larger, split the build or check the config into a controlled branch and add a repository-based config path instead of pasting the payload.

Reduced operator artifacts are not general-purpose ORT builds. When a config is supplied, archive and upload names include `ops-<12-hex-chars>`, and `manifest.json` records `reduced_ops`, the full `required_operators_config_sha256`, and safe counts. To correlate a local config with an artifact, run `shasum -a 256 required_operators.config` and match the first 12 hex characters to the artifact name or the full hash in the manifest.

## Local Validation

Run these lightweight checks before committing maintenance or build-orchestration changes:

```bash
./build.sh --dry-run
bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh
python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py
git diff --check
```

When workflow files change, also parse the YAML and run `actionlint`:

```bash
ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file) }' .github/workflows/*.yml
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml
```

For CMake flag, provider, patch, packaging, or release changes, run the smallest representative configure or build that proves the behavior. If a platform runner is unavailable locally, document that limitation in the completion log and rely on the matching GitHub Actions run after push.

## Patch Maintenance

ONNX Runtime patches live under `src/patches/all/` and version-specific directories such as `src/patches/all-v1.22/`. Keep patches small, ordered by filename, tied to the ONNX Runtime versions they apply to, and easy to rebase.

CMake validates each patch with `git apply --check --ignore-whitespace --recount` before applying it, then runs `scripts/verify_onnxruntime_patches.cmake`. When changing patches, validate against the matching ONNX Runtime source or run a targeted local configure/build that exercises the patch set.
