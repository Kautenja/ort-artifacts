# Simplify CD Workflow Dispatch Inputs

## Decisions
- Removed the manual `publish` input and the `publish` job from `.github/workflows/cd.yml`; `_publish.yml` and manifest generation remain unchanged for future reusable publishing work.
- Removed the manual `target-all` input and the `TARGET_ALL` branch from the selector.
- Defaulted every individual target checkbox to `true`, preserving the full-build default while always passing an explicit comma-separated target list to `_build.yml`.
- Updated README examples so CLI users know omitted target inputs keep their true defaults.

## Lessons Learned
- With default-true target inputs, narrow `gh workflow run` invocations must explicitly set non-selected targets to `false`.
- The resolver's internal `targets=all` support remains useful for reusable or future callers, but the manual CD workflow no longer emits it.

## Validation Performed
- `awk 'BEGIN { n = 0 } /^      [A-Za-z0-9_-]+:$/ { n++ } END { print "workflow_dispatch input count:", n; exit (n > 25 || n != 24) }' .github/workflows/cd.yml`
- Local Python workflow-default check verified 24 inputs, no `publish`/`target-all` inputs, every selectable target defaulting to `true`, default target resolution matching `resolve_targets("all")`, `apple-xcframework` prerequisite expansion, and empty-selection failure.
- `PYTHONPATH=.github/scripts python3 -m unittest discover -s .github/scripts -p 'test_resolve_build_targets.py'`
- `PYTHONPATH=.github/scripts python3 -m unittest discover -s .github/scripts`
- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py .github/scripts/validate_required_operators_config.py .github/scripts/resolve_build_targets.py .github/scripts/create_apple_universal_static_artifact.py .github/scripts/create_apple_xcframework_artifact.py .github/scripts/slim_windows_artifact.py`
- `ruby -e 'require "yaml"; ARGV.each { |file| YAML.load_file(file); puts "parsed #{file}" }' .github/workflows/*.yml`
- `go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 .github/workflows/cd.yml .github/workflows/_build.yml .github/workflows/_publish.yml`
- `git diff --check`

## Issues Encountered
- A first `unittest` invocation used a file path where `unittest` expected an importable test name; reran with discovery and the resolver tests passed.
- Ruby emitted an existing local `ffi` gem warning while parsing YAML, but returned success and parsed all workflows.
