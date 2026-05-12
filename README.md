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
