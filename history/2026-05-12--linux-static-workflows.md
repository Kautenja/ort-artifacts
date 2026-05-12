# Linux Static Artifact Workflows

## Decisions

- Enabled `linux-x86_64-static` and `linux-aarch64-static` in the reusable build matrix.
- Kept Linux execution providers aligned with the existing disabled target plan: XNNPACK and OpenVINO.
- Used the upstream ONNX Runtime ARM64 Linux toolchain file and passed `CMAKE_SYSTEM_PROCESSOR`, `CMAKE_SYSROOT`, and `CMAKE_FIND_ROOT_PATH` into the ExternalProject configure command for aarch64.
- Exposed both Linux targets in the manual CD workflow target preset choices.

## Lessons Learned

- The disabled Linux workflow path already had most packaging and OpenVINO setup in place, but the clang install step needed noninteractive apt flags before activation.
- The repository's manifest generator is target-name agnostic and correctly includes Linux zip names, SHA256 checksums, the static ONNX Runtime library, and extra OpenVINO shared libraries.

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
- Temporary Linux x86_64 CMake configure: `cmake -S . -B /tmp/ort-artifacts-linux-x86_64-config -DSTATIC_BUILD=ON -DTARGET_ARCH=x86_64 -DUSE_XNNPACK=ON -DUSE_OPENVINO=ON -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_BUILD_TYPE=Release`
- Temporary Linux aarch64 CMake configure: `CMAKE_SYSROOT=/opt/linaro-toolchain/aarch64-none-linux-gnu/libc CMAKE_FIND_ROOT_PATH=/opt/linaro-toolchain/aarch64-none-linux-gnu cmake -S . -B /tmp/ort-artifacts-linux-aarch64-config -DSTATIC_BUILD=ON -DTARGET_ARCH=aarch64 -DUSE_XNNPACK=ON -DUSE_OPENVINO=ON -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_BUILD_TYPE=Release`
- Verified generated ExternalProject configure commands include Linux OpenVINO/XNNPACK arguments for both targets and ARM64 toolchain, processor, sysroot, and find-root arguments for aarch64.
- Created representative Linux zip archives in `/tmp/ort-artifacts-manifest-linux` and verified `generate_manifest.py` emits Linux archive names and SHA256 checksums.

## Issues Encountered

- `gh` is not installed in this environment, so a manual GitHub Actions dispatch could not be started locally. Temporary local Linux CMake configure checks were used as the local equivalent required by the spec.
- `actionlint@latest` requires a newer Go directive than the installed Go tool accepts; `actionlint@v1.7.7` ran successfully.
