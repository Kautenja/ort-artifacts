# ONNX Runtime Artifacts Constitution
> Build and publish reproducible ONNX Runtime artifacts for selected platforms, architectures, build modes, and execution providers.

---

## Context Detection

**Ralph Loop Mode** (started by `scripts/ralph-loop*.sh`):
- Read this file before making changes.
- Pick the highest-priority incomplete spec from `specs/` unless `IMPLEMENTATION_PLAN.md` exists.
- Implement one work item completely, verify acceptance criteria, commit, and push.
- Output `<promise>DONE</promise>` only when the selected work item is complete.
- Output `<promise>ALL_DONE</promise>` when no incomplete work remains.

**Interactive Mode** (normal conversation):
- Be helpful, explain tradeoffs, and create or refine specs before implementation.
- Use the same project principles, but ask for clarification when product or release intent is ambiguous.

---

## Core Principles

1. Reproducible artifact builds: build inputs, references, patches, and release outputs must be explicit and repeatable.
2. Cross-platform correctness: changes must account for macOS, iOS, simulator, Windows, Linux, Android, and WebAssembly implications when relevant.
3. Minimal patch surface: keep ONNX Runtime patches focused, documented by file name, and easy to rebase across upstream versions.
4. CI-first verification: prefer validation that matches GitHub Actions and preserves expensive platform builds for targeted cases.
5. Simple maintenance: avoid abstractions that hide CMake, shell, or workflow behavior without reducing real complexity.

---

## Technical Stack

- Build orchestration: Bash (`build.sh`) and CMake `ExternalProject`.
- Source artifacts: ONNX Runtime source fetched by CMake, patched from `src/patches/`.
- Platforms: macOS, iOS, iOS simulator, with dormant support paths for Linux, Windows, Android, and WebAssembly.
- CI/CD: GitHub Actions workflows in `.github/workflows/`.
- Release metadata: Python manifest generation in `.github/scripts/generate_manifest.py`.
- Primary validation: `./build.sh --dry-run`, shell syntax checks, targeted CMake/build runs, and GitHub Actions.

---

## Autonomy

YOLO Mode: ENABLED
Git Autonomy: ENABLED

Agents may edit files, run local validation, commit, and push during Ralph Loop Mode. Do not use destructive cleanups such as removing build directories unless the active spec explicitly requires it or the cleanup is clearly part of the validation workflow.

---

## Ralph Installation

- Upstream: `https://github.com/fstandhartinger/ralph-wiggum`
- Installed from upstream commit: `3f15f0fb83b8c2e0ac8d11abdae0e83ab8204981`
- Installed on: `2026-05-12`
- Primary local loop: `./scripts/ralph-loop-codex.sh`

---

## Specs

Specs live in `specs/` as numbered markdown files. Lower numbers have higher priority.

A root-level spec is incomplete unless it contains one of:
- `Status: COMPLETE`
- `**Status**: COMPLETE`
- `## Status: COMPLETE`

Use `templates/spec-template.md` for new specs. Each spec must include specific, testable acceptance criteria and a completion signal section.

---

## NR_OF_TRIES

Track attempts per spec with an `NR_OF_TRIES` comment at the bottom of the spec file.

Increment the count when starting a spec. At 10 attempts, treat the spec as stuck and split it into smaller specs before continuing.

---

## History

After each completed spec:
- Append a one-line summary to `history.md`.
- Create `history/YYYY-MM-DD--spec-name.md` with decisions, lessons learned, validation performed, and issues encountered.
- Check `history/` before retrying a spec with previous attempts.

---

## Completion Logs

After each completed spec, create `completion_log/YYYY-MM-DD--HH-MM-SS--spec-name.md` with a brief summary of the change, validation, and commit.

---

## Validation Commands

Start with lightweight checks:

```bash
./build.sh --dry-run
bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh
python3 -m py_compile .github/scripts/generate_manifest.py
```

For changes that affect CMake flags, patches, platform behavior, packaging, or release outputs, run the smallest representative local configure/build that proves the change. If local platform dependencies are unavailable, document that limitation in the completion log and rely on the matching GitHub Actions workflow after push.

---

## Completion Signal

All acceptance criteria verified, validation completed or explicitly documented, changes committed and pushed:

`<promise>DONE</promise>`

Never output the completion signal until the selected work item is genuinely complete.
