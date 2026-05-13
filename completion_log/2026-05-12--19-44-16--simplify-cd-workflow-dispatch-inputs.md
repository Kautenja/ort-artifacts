# Simplify CD Workflow Dispatch Inputs

## Summary
- Removed the manual `publish` and `target-all` workflow dispatch inputs from `.github/workflows/cd.yml`.
- Removed the `inputs.publish`-gated publish job and the selector's `TARGET_ALL` branch.
- Defaulted all individual target checkboxes to `true` and kept `_build.yml` receiving explicit target lists from the manual workflow.
- Updated README guidance and the empty-selection message to match the new manual dispatch model.

## Validation
- Verified `.github/workflows/cd.yml` has 24 dispatch inputs and no removed `publish` or `target-all` manual inputs.
- Verified default checkbox state resolves to the same build, universal, and XCFramework target sets as the internal `all` alias.
- Verified `apple-xcframework` selected alone still expands required source artifacts.
- Verified empty target selection fails with `No build targets selected. Select at least one target checkbox.`
- Ran resolver tests, full `.github/scripts` unittest discovery, dry-run build, shell syntax checks, Python compilation, YAML parse, actionlint, and `git diff --check`.
