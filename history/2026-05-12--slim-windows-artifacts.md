# Slim Windows Artifacts

## Decisions

- Measured GitHub Actions artifact `ort-v1.22.2-windows-md-x86_64-static-release` from artifact ID `6957249093`.
- The downloaded artifact was an upload-artifact wrapper zip containing the release archive. Inner archive size was `81,546,260` bytes.
- Inner archive contents were only:
  - `onnxruntime/lib/onnxruntime.lib`: `676,718,430` bytes uncompressed, `81,545,784` bytes compressed.
- Top-level inventory: `onnxruntime` contained 1 file, `676,718,430` bytes uncompressed and `81,545,784` bytes compressed.
- Area inventory for the measured Release archive:
  - `onnxruntime/lib`: 1 file, `676,718,430` bytes uncompressed, `81,545,784` bytes compressed.
  - `onnxruntime/bin`: 0 files.
  - `.lib`: 1 file, `676,718,430` bytes uncompressed, `81,545,784` bytes compressed.
  - `.dll`: 0 files.
  - `.pdb`: 0 files.
  - CMake package metadata: 0 files.
- No Debug Windows artifact was available in the current artifact list, so Release and Debug could not be compared from real CI outputs.
- The measured Release artifact had no PDB payload to remove safely; its size was the bundled MSVC static library. The safe reduction is therefore a guardrail: Release PDB files are omitted or removed when they appear, while the required static library remains intact.
- Required files are `onnxruntime/lib/onnxruntime.lib` for Release or `onnxruntime/lib/onnxruntimed.lib` for Debug, public headers under `onnxruntime/include`, CMake package files under `onnxruntime/lib/cmake/onnxruntime`, and `DirectML.dll`/`DirectML.Debug.dll` when DirectML is enabled.
- Debug PDB files are diagnostic-only. Release PDB files are intentionally excluded from the main consumer archive rather than emitted as a separate symbol artifact.

## Implementation

- Added `.github/scripts/slim_windows_artifact.py` to validate Windows staging directories, classify files, require headers/CMake metadata/DirectML DLLs, and remove Release `.pdb` files.
- Added unit tests for Release PDB removal, Debug PDB preservation, and DirectML DLL validation.
- Updated `_build.yml` to run the slimming validator before archiving Windows artifacts.
- Updated static-build installation to include public headers and a minimal relocatable CMake package.
- Updated DirectML install rules and patches so Release installs `DirectML.dll` without `DirectML.pdb`, while Debug may install `DirectML.Debug.dll` and `DirectML.Debug.pdb`.
- Updated README Windows artifact notes and local validation commands.

## Validation

- `./build.sh --dry-run`
- `./build.sh --dry-run --static --directml --xnnpack -N`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py`
- `python3 .github/scripts/test_slim_windows_artifact.py`
- `python3 -m unittest discover -s .github/scripts -p 'test_*.py'`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file) }' .github/workflows/*.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml`
- `git diff --check`
- Local CMake generation equivalent on macOS: `cmake -S . -B /tmp/ort-artifacts-spec007/cmake-config --compile-no-warning-as-error -DREFERENCE=v1.22.2 -DSTATIC_BUILD=ON -DCMAKE_BUILD_TYPE=Release -DTARGET_ARCH=x86_64 -DUSE_XNNPACK=ON`
- Representative slimmed Windows fixture:
  - Baseline staged bytes with `DirectML.pdb`: `65,570`.
  - Slimmed staged bytes after Release PDB removal: `34`.
  - Slimmed zip retained `onnxruntime/lib/onnxruntime.lib`, public header, CMake config/targets files, and `onnxruntime/bin/DirectML.dll`.
  - `generate_manifest.py` produced a Windows entry with `archive`, `sha256`, `lib_dir`, `ort_lib`, and `extra_files` containing `onnxruntime/bin/DirectML.dll`.

## Issues

- A real Windows configure/build was not run locally because this machine is macOS and lacks the Windows runner/MSVC/DirectML environment. The workflow validation step is intended to enforce the Windows-specific package layout after the next GitHub Actions Windows build.
- An attempted local Ninja configure showed Ninja is not installed; the successful local CMake generation used the default macOS generator instead.
