# Single Visible CD Workflow

## Summary

Inlined the reusable build workflow into `.github/workflows/cd.yml`, removed the internal `_build.yml` and `_publish.yml` workflow files, and preserved build behavior through buildtype-expanded resolver matrices.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/resolve_build_targets.py .github/scripts/validate_required_operators_config.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_resolve_build_targets.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_create_apple_universal_static_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_create_apple_xcframework_artifact.py`
- `PYTHONPATH=.github/scripts python3 .github/scripts/test_slim_windows_artifact.py`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file); puts "parsed #{file}" }' .github/workflows/*.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml`
- `git diff --check`
- Local workflow checks for only `cd.yml`, no `workflow_call`, no local workflow `uses`, and no active `name: Build` or `name: Publish`.
- Local dispatch input-count check reported 24 inputs.
- Resolver checks verified empty target selection fails and `Debug`, `Release`, and `Both` produce expected matrix counts.
- Artifact-name checks verified representative normal and reduced-operator names still match the prior format.

## Notes

- `.github/scripts/generate_manifest.py` was left intact.
- Full platform builds were not run locally; platform-specific behavior remains covered by GitHub Actions after push.
