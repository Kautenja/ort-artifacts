# ONNX Runtime Artifacts

Builds of [ONNX runtime](https://github.com/microsoft/onnxruntime) for various platforms.

## Ralph Wiggum Workflow

This repository is configured for the Ralph Wiggum autonomous spec loop. Agents should read `.specify/memory/constitution.md` before working.

Create work as specs in `specs/`, then run:

```bash
./scripts/ralph-loop-codex.sh
```

Useful variants:

```bash
./scripts/ralph-loop-codex.sh plan
./scripts/ralph-loop-codex.sh 20
```

The loop writes runtime logs under `logs/` and generated prompt files at the repository root; both are ignored by git.

## Build Targets

The CD workflow can build all enabled targets or one target preset at a time. Enabled static artifact targets are:

- `linux-x86_64-static`: native Ubuntu x86_64 build with XNNPACK and OpenVINO.
- `linux-aarch64-static`: Ubuntu-hosted aarch64 cross build with XNNPACK and OpenVINO.
- `macos-x86_64-static`: macOS x86_64 build with XNNPACK and Core ML.
- `macos-aarch64-static`: macOS arm64 build with XNNPACK and Core ML.
- `ios-aarch64-static`: iOS device arm64 build with XNNPACK and Core ML.
- `ios-simulator-aarch64-static`: iOS simulator arm64 build with XNNPACK and Core ML.
- `ios-simulator-x86_64-static`: iOS simulator x86_64 build with XNNPACK and Core ML.
- `windows-md-x86_64-static`: Windows x64 build with DirectML, XNNPACK, and the dynamic MSVC runtime (`/MD`).
- `android-arm64-v8a-static`: Android arm64-v8a native static build with XNNPACK and NNAPI.
- `android-armeabi-v7a-static`: Android armeabi-v7a native static build with XNNPACK and NNAPI.
- `android-x86_64-static`: Android x86_64 native static build with XNNPACK and NNAPI.
- `android-x86-static`: Android x86 native static build with XNNPACK and NNAPI.

Windows static artifacts currently enable the dynamic CRT target only. The static CRT variant and Windows ARM64 are deferred to later specs so they can receive separate runner, toolchain, and downstream-linking validation.

Android artifacts are native static archives for downstream CMake/JNI integration. They do not package ONNX Runtime Java bindings, `onnxruntime4j`, or an AAR; JNI bindings are expected to live in the consuming project.

## Reduced Operator Builds

Manual CD runs can build model-set-specific ONNX Runtime artifacts from a reduced operator config. Generate a config from ONNX Runtime tooling, for example with `create_reduced_build_config.py`, or keep the `required_operators.config` / `required_operators_and_types.config` emitted when converting ONNX models to ORT format. Type-aware configs can be used with `enable-reduced-operator-type-support`.

Base64 encode the config before starting the workflow. The raw config is decoded only under the runner temp directory and is not uploaded.

macOS/Linux:

```bash
base64 -i required_operators.config | tr -d '\n'
```

Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("required_operators.config"))
```

In the GitHub Actions UI, choose **CD**, select **Run workflow**, paste the base64 string into `required-operators-config-base64`, and enable `enable-reduced-operator-type-support` only for a type-aware config. The same run can leave `target-custom` empty, or set it to a substring filter for one target.

CLI example:

```bash
gh workflow run cd.yml \
  -f target-preset=linux-x86_64-static \
  -f target-custom= \
  -f buildtype=Release \
  -f required-operators-config-base64="$(base64 -i required_operators.config | tr -d '\n')" \
  -f enable-reduced-operator-type-support=false
```

GitHub `workflow_dispatch` inputs are limited to 65,535 characters. If the generated base64 payload is larger, split the build or check the config into a controlled branch and add a repository-based config path instead of pasting the payload.

Reduced operator artifacts are not general-purpose ORT builds. When a config is supplied, archive and upload names include `ops-<12-hex-chars>`, and `manifest.json` records `reduced_ops`, the full `required_operators_config_sha256`, and safe counts. To correlate a local config with an artifact, run `shasum -a 256 required_operators.config` and match the first 12 hex characters to the artifact name or the full hash in the manifest.
