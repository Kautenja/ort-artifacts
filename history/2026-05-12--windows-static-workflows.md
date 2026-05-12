# Windows Static Artifact Workflows

## Summary

- Enabled `windows-md-x86_64-static` in the reusable build workflow and CD dispatch presets.
- Selected the dynamic MSVC runtime (`/MD`) for the first Windows artifact and deferred the static CRT variant.
- Deferred Windows ARM64 to a later spec, while documenting that x86_64 is the required target for this phase.
- Kept Windows OpenVINO disabled until its hosted-runner install and link path is proven.

## Decisions

- Use `windows-2022` because ONNX Runtime documents Visual Studio 2022 as the supported Windows CMake generator and GitHub lists `windows-2022` as an x64 hosted runner.
- Use DirectML and XNNPACK for the selected Windows target; do not include OpenVINO on Windows in this phase.
- Add a Windows tool verification step for CMake, Ninja, 7-Zip, and Visual Studio VC tools before invoking `build.sh`.
- Fix the Windows 7-Zip packaging command to archive `build/artifact` contents explicitly.

## Lessons Learned

- The manifest generator is target-name agnostic and already recognizes `onnxruntime.lib` plus Windows extras such as `.pdb`.
- Local macOS validation can verify `build.sh` argument plumbing and release metadata, but it cannot prove a Windows hosted-runner compile.

## Validation Performed

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `./build.sh --dry-run --static --directml --xnnpack -N`
- `./build.sh --dry-run --static --mt --directml --xnnpack -N`
- Ruby YAML parse for `.github/workflows/_build.yml`, `.github/workflows/cd.yml`, and `.github/workflows/_publish.yml`.
- Extracted workflow `run` snippets and checked them with `bash -n` after substituting GitHub expressions.
- Ruby assertion that `_build.yml` contains only the selected active Windows target and `cd.yml` exposes it as a dispatch preset.
- `cmake -S . -B /tmp/ort-artifacts-windows-spec-config -DSTATIC_BUILD=ON -DUSE_XNNPACK=ON -DCMAKE_BUILD_TYPE=Release`
- Representative Windows zip manifest test with `onnxruntime/lib/onnxruntime.lib` and `onnxruntime/lib/onnxruntime.pdb`.

## Issues Encountered

- `gh` is not installed on this machine, so the Windows GitHub Actions build was not dispatched from the local loop. Follow-up command after installing/authenticating `gh`:

```bash
gh workflow run cd.yml --repo Kautenja/ort-artifacts --ref ralph-dev -f onnxruntime-ref=v1.22.2 -f target-preset=windows-md-x86_64-static -f target-custom= -f buildtype=Release -f publish=false
```

- 7-Zip is not installed on this macOS host, so the Windows-specific archive command could not be executed locally. The workflow now checks `7z` on the Windows runner before building.

## Sources Consulted

- GitHub hosted runner reference: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- ONNX Runtime build for inferencing docs: https://onnxruntime.ai/docs/build/inferencing.html
