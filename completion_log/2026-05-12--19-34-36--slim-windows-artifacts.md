# Slim Windows Artifacts

## Summary

Completed `specs/007-slim-windows-artifacts.md`.

The measured Release Windows artifact from GitHub Actions contained only `onnxruntime/lib/onnxruntime.lib`:

- Inner archive size: `81,546,260` bytes.
- `onnxruntime/lib/onnxruntime.lib`: `676,718,430` bytes uncompressed, `81,545,784` bytes compressed.
- `onnxruntime/bin`: 0 files.
- `.dll`: 0 files.
- `.pdb`: 0 files.
- CMake/package metadata: 0 files.

Because no PDB files were present in that real Release artifact, there was no safe direct reduction to make from the measured archive; the bulk is the required static library. The implementation adds guardrails so Release Windows archives exclude PDB files when they appear, while preserving required link/runtime files.

## Changes

- Added `.github/scripts/slim_windows_artifact.py` and tests.
- Added Windows staging validation to `.github/workflows/_build.yml`.
- Installed public headers and minimal CMake package metadata from `src/static-build`.
- Changed DirectML install rules so Release keeps the DLL and omits PDBs, while Debug can retain Debug PDBs.
- Updated README and marked spec 007 complete.

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
- `cmake -S . -B /tmp/ort-artifacts-spec007/cmake-config --compile-no-warning-as-error -DREFERENCE=v1.22.2 -DSTATIC_BUILD=ON -DCMAKE_BUILD_TYPE=Release -DTARGET_ARCH=x86_64 -DUSE_XNNPACK=ON`
- Representative slimmed Windows fixture validated PDB removal, required headers/CMake metadata, DirectML DLL preservation, and manifest generation.

## Notes

- Real Windows configure/build remains a GitHub Actions verification because local macOS cannot provide the Windows/MSVC/DirectML environment.
- No separate symbol artifact was introduced; Release PDBs are intentionally excluded from the main archive.
