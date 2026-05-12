# Required Operators Config Workflow

## Summary

Implemented model-specific reduced operator artifact support for manual CD runs. The workflow accepts a base64 required-operators config, decodes and validates it under runner temp, passes it into `build.sh`, runs ONNX Runtime's reduced kernel generation before ExternalProject configure, and distinguishes reduced artifacts with `ops-<hash>` names plus manifest metadata.

## Validation

- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py`
- Validator CLI checks covered valid config, base64 decode, invalid base64, malformed config, and incompatible type-reduction/global-type config.
- `./build.sh --dry-run`
- `./build.sh --dry-run --static --required-operators-config <sample-file> -N`
- `./build.sh --dry-run --enable-reduced-operator-type-support` failed early with the expected clear error.
- Temporary CMake configure and `rg` verified `reduce_op_kernels.py`, `--enable_type_reduction`, and `-Donnxruntime_REDUCED_OPS_BUILD=ON` in generated ExternalProject commands.
- `ruby -e 'require "yaml"; ARGV.each { |f| YAML.load_file(f); puts "parsed #{f}" }' .github/workflows/_build.yml .github/workflows/cd.yml .github/workflows/_publish.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/_build.yml .github/workflows/cd.yml .github/workflows/_publish.yml`
- Temporary manifest generation verified reduced metadata and full-artifact behavior.
- `git diff --check`

## Notes

Config correlation is documented in the README: compute `shasum -a 256 required_operators.config`, match the first 12 hex characters to the `ops-<hash>` artifact marker, or match the full SHA256 in `manifest.json`.

## Limitations

No live GitHub-hosted runner build was dispatched locally. The pushed workflow should perform the target-specific build execution.
