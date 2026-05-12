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

Windows static artifacts currently enable the dynamic CRT target only. The static CRT variant and Windows ARM64 are deferred to later specs so they can receive separate runner, toolchain, and downstream-linking validation.
