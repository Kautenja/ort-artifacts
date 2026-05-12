# Execution Provider Workflow Checkboxes

## Summary

Added manual CD workflow checkboxes for XNNPACK, OpenVINO, DirectML, CoreML, and NNAPI. The reusable build workflow now receives those provider inputs, resolves the selected target matrix, and removes provider flags when a checkbox is disabled or a target is not compatible.

## Decisions

- Preserved the existing default build arguments exactly for every active target when all provider inputs use their defaults.
- Kept target and artifact names unchanged even when a provider is disabled, matching the spec's initial implementation guidance.
- Used target-specific compatible provider lists in `_build.yml` so DirectML, CoreML, NNAPI, and OpenVINO cannot be added to unsupported platforms through global defaults.
- Left WebGPU intentionally unexposed because no active workflow target currently enables or supports it; `build.sh --webgpu` remains available for future explicit build paths.
- Kept OpenVINO install, verification, and rpath repair gated on `contains(matrix.args, '--openvino')`, so disabling OpenVINO removes the setup path.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- Ruby YAML parse for `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- Downloaded `actionlint` 1.7.12 release binary and linted `.github/workflows/cd.yml`, `.github/workflows/_build.yml`, and `.github/workflows/_publish.yml`
- Extracted and executed the `_build.yml` target resolver to verify default arguments, each disabled provider, incompatible target/provider selections, all-provider-off baseline arguments, and representative Linux, Apple, Windows, and Android targets.
- Ran representative `./build.sh --dry-run` commands for Linux with XNNPACK/OpenVINO, macOS with XNNPACK/CoreML, iOS simulator with XNNPACK/CoreML, Windows with DirectML/XNNPACK, and Android with XNNPACK/NNAPI.
- `rg` verified OpenVINO setup and rpath steps are gated by the effective `matrix.args` OpenVINO flag.
- `git diff --check`

## Issues

- No live GitHub Actions build was dispatched locally. Workflow syntax, target argument generation, and local dry-run behavior were validated; runner-specific builds will execute after push.
