# Linux Static Artifact Workflows

## Summary

Enabled static Linux ONNX Runtime artifact workflows for `linux-x86_64-static` and `linux-aarch64-static`, exposed both targets in CD workflow dispatch, added explicit ARM64 cross-compilation cache values, and documented enabled Linux targets in the README.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `ruby -e 'require "yaml"; ARGV.each { |f| YAML.load_file(f); puts "parsed #{f}" }' .github/workflows/_build.yml .github/workflows/cd.yml .github/workflows/_publish.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/_build.yml .github/workflows/cd.yml .github/workflows/_publish.yml`
- `./build.sh --dry-run --static --xnnpack -N --openvino`
- `./build.sh --dry-run --static -A aarch64 --xnnpack -N --openvino`
- `TARGET_LINUX=true ./build.sh --dry-run --static --xnnpack -N --openvino`
- `TARGET_LINUX=true CMAKE_SYSROOT=/opt/linaro-toolchain/aarch64-none-linux-gnu/libc CMAKE_FIND_ROOT_PATH=/opt/linaro-toolchain/aarch64-none-linux-gnu ./build.sh --dry-run --static -A aarch64 --xnnpack -N --openvino`
- Temporary Linux x86_64 CMake configure succeeded in `/tmp/ort-artifacts-linux-x86_64-config`.
- Temporary Linux aarch64 CMake configure succeeded in `/tmp/ort-artifacts-linux-aarch64-config`.
- Verified generated ExternalProject configure commands for Linux x86_64 and aarch64.
- Verified representative Linux zip archives are included by `.github/scripts/generate_manifest.py` with archive names and SHA256 checksums.

## Limitations

- `gh` is not installed in this environment, so a manual GitHub Actions workflow dispatch could not be started from the local machine. Local Linux CMake configure checks were used instead.
