# Required Operators Config Workflow

## Summary

Added optional reduced-operator config inputs to the CD workflow, reusable workflow decode and validation under runner temp, `build.sh` and CMake propagation, ONNX Runtime reduced-kernel generation, reduced artifact hash markers, manifest metadata, and README usage instructions.

## Decisions

- Decoded the base64 config under `$RUNNER_TEMP` and validated it with `.github/scripts/validate_required_operators_config.py` so raw config contents are not printed or uploaded.
- Matched the ONNX Runtime v1.22.2 build flow by running `tools/ci_build/reduce_op_kernels.py` before ExternalProject configure and setting `onnxruntime_REDUCED_OPS_BUILD=ON` only for reduced builds.
- Passed reduced type support only to the ORT reduction step (`--enable_type_reduction`) and failed early when requested without a config.
- Wrote safe archive metadata to `onnxruntime/reduced_operators.json` so `manifest.json` can include the full config SHA256 without publishing the raw config.
- Kept full-operator artifact names unchanged; reduced artifacts add `ops-<12-hex-chars>`.

## Validation

- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py`
- Command-line validator checks for valid standard/type configs, base64 decode, invalid base64, malformed config, and mutually exclusive type filters.
- `./build.sh --dry-run`
- `./build.sh --dry-run --static --required-operators-config <sample-file> -N`
- `./build.sh --dry-run --enable-reduced-operator-type-support` verified clear early failure without a config.
- Temporary CMake configure verified generated ExternalProject commands include `reduce_op_kernels.py`, `--enable_type_reduction`, and `-Donnxruntime_REDUCED_OPS_BUILD=ON`.
- Ruby YAML parse and `actionlint` passed for `_build.yml`, `cd.yml`, and `_publish.yml`.
- Temporary archive manifest test verified full artifacts report `reduced_ops: false` and reduced artifacts include the full config SHA256.
- `git diff --check`

## Issues

- A live GitHub-hosted target build was not started from this local environment. Runner-specific execution is left to the pushed workflow; the reusable workflow syntax, generated build commands, and manifest behavior were validated locally.
