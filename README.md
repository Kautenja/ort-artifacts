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

The CD workflow can build all enabled targets or one target preset at a time. Enabled static Linux artifact targets are:

- `linux-x86_64-static`: native Ubuntu x86_64 build with XNNPACK and OpenVINO.
- `linux-aarch64-static`: Ubuntu-hosted aarch64 cross build with XNNPACK and OpenVINO.
