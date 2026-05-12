# Windows Static Artifact Workflows

## Summary

Completed `specs/002-windows-static-workflows.md` by enabling the `windows-md-x86_64-static` target, adding it to CD dispatch presets, documenting dynamic-CRT-only scope, and deferring Windows ARM64/static CRT to later specs.

## Validation

- `./build.sh --dry-run`
- `bash -n build.sh scripts/ralph-loop.sh scripts/ralph-loop-codex.sh scripts/ralph-loop-gemini.sh scripts/ralph-loop-copilot.sh scripts/lib/spec_queue.sh scripts/lib/nr_of_tries.sh`
- `python3 -m py_compile .github/scripts/generate_manifest.py`
- `./build.sh --dry-run --static --directml --xnnpack -N`
- `./build.sh --dry-run --static --mt --directml --xnnpack -N`
- Ruby YAML parse for workflow files.
- Workflow Bash snippets checked with `bash -n` after GitHub expression substitution.
- Workflow target/preset assertions for `windows-md-x86_64-static`.
- Local CMake configure: `cmake -S . -B /tmp/ort-artifacts-windows-spec-config -DSTATIC_BUILD=ON -DUSE_XNNPACK=ON -DCMAKE_BUILD_TYPE=Release`
- Representative Windows archive manifest generation and assertions for archive name, SHA256, `onnxruntime.lib`, and `.pdb` extra file metadata.

## Platform Limitations

- A Windows GitHub Actions build was not dispatched because `gh` is not installed locally. Exact follow-up:

```bash
gh workflow run cd.yml --repo Kautenja/ort-artifacts --ref ralph-dev -f onnxruntime-ref=v1.22.2 -f target-preset=windows-md-x86_64-static -f target-custom= -f buildtype=Release -f publish=false
```

- Local 7-Zip is unavailable on this macOS host; the Windows workflow now verifies `7z` on the hosted runner before building and packaging.

## Sources Consulted

- GitHub hosted runner reference: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- ONNX Runtime build for inferencing docs: https://onnxruntime.ai/docs/build/inferencing.html
