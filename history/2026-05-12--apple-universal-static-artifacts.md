# Apple Universal Static Artifacts

## Summary

Added derived universal Apple static artifacts for macOS and iOS simulator. The CD workflow now exposes `macos-universal-static` and `ios-simulator-universal-static` checkboxes, and the reusable build workflow expands those selections into the matching aarch64 and x86_64 source builds before packaging the universal archives with `lipo`.

## Decisions

- Moved target matrix resolution into `.github/scripts/resolve_build_targets.py` so workflow behavior and local tests share the same target rules.
- Kept existing architecture-specific Apple targets unchanged; universal targets are derived packaging outputs and never trigger a third ONNX Runtime compile.
- Used `.github/scripts/create_apple_universal_static_artifact.py` to extract both source zips, compare layouts, compare public headers, compare reduced-operator metadata, run `lipo -create`, verify the expected architectures, and repackage the normal `onnxruntime` layout.
- Preserved reduced-operator artifact naming by recomputing the same `ops-<12-hex-chars>` marker in the universal packaging job.
- Added manifest `artifact` and `lib_dir` fields so universal archives record artifact name, library directory, and primary library path without changing manifest keys for existing targets.
- Added a scoped actionlint configuration for the existing checkbox-heavy CD workflow dispatch input count rule, while keeping all other workflow lint checks active.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/test_resolve_build_targets.py .github/scripts/test_create_apple_universal_static_artifact.py`
- `python3 .github/scripts/test_resolve_build_targets.py`
- `python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- Ruby YAML parse for `.github/workflows/*.yml` and `.github/actionlint.yaml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml`
- `git diff --check`
- Resolver CLI checks for `target-all`, each universal target selected alone, both macOS source slices without the universal target, and missing universal prerequisites.

## Issues

- No full ONNX Runtime Apple CI build was dispatched from the local loop. Local fixture builds used real macOS and iOS simulator static archives, combined them with `lipo`, verified `lipo -info`, checked headers and reduced-operator metadata, and exercised manifest generation.
- The follow-up XCFramework consumer validation remains intentionally deferred to `specs/010-apple-xcframework-artifact.md`.
