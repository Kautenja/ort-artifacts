#!/usr/bin/env python3
"""Validate and slim a staged Windows ONNX Runtime artifact."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List


class WindowsArtifactError(ValueError):
    """A packaging error that is safe to print in GitHub Actions logs."""


@dataclass(frozen=True)
class InventoryEntry:
    path: str
    size: int
    classification: str
    reason: str


def relative_files(root: Path) -> List[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def relative_name(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def file_size(path: Path) -> int:
    return path.stat().st_size


def top_level_inventory(root: Path, files: Iterable[Path]) -> dict[str, dict[str, int]]:
    inventory: dict[str, dict[str, int]] = {}
    for path in files:
        relative = relative_name(root, path)
        top = relative.split("/", 1)[0]
        entry = inventory.setdefault(top, {"files": 0, "bytes": 0})
        entry["files"] += 1
        entry["bytes"] += file_size(path)
    return inventory


def size_by_predicate(files: Iterable[Path], predicate) -> dict[str, int]:
    selected = [path for path in files if predicate(path)]
    return {
        "files": len(selected),
        "bytes": sum(file_size(path) for path in selected),
    }


def find_primary_library(root: Path, buildtype: str) -> Path:
    library_name = "onnxruntimed.lib" if buildtype.lower() == "debug" else "onnxruntime.lib"
    library = root / "onnxruntime" / "lib" / library_name
    if library.is_file():
        return library
    raise WindowsArtifactError(f"Required primary ONNX Runtime library is missing: {library}")


def find_headers(root: Path) -> List[Path]:
    include_root = root / "onnxruntime" / "include"
    return sorted(
        path
        for pattern in ("*.h", "*.hpp")
        for path in include_root.rglob(pattern)
        if path.is_file()
    )


def find_cmake_package_files(root: Path) -> List[Path]:
    cmake_root = root / "onnxruntime" / "lib" / "cmake" / "onnxruntime"
    return sorted(path for path in cmake_root.glob("*.cmake") if path.is_file())


def find_directml_dlls(root: Path) -> List[Path]:
    bin_root = root / "onnxruntime" / "bin"
    if not bin_root.exists():
        return []
    return sorted(
        path
        for path in bin_root.iterdir()
        if path.is_file() and path.name.lower() in {"directml.dll", "directml.debug.dll"}
    )


def classify_file(root: Path, path: Path, primary_library: Path, expect_directml: bool) -> InventoryEntry:
    relative = relative_name(root, path)
    suffix = path.suffix.lower()
    lower_name = path.name.lower()

    if path == primary_library:
        return InventoryEntry(relative, file_size(path), "required", "primary ONNX Runtime static library")
    if relative.startswith("onnxruntime/include/") and suffix in {".h", ".hpp"}:
        return InventoryEntry(relative, file_size(path), "required", "public downstream header")
    if relative.startswith("onnxruntime/lib/cmake/onnxruntime/") and suffix == ".cmake":
        return InventoryEntry(relative, file_size(path), "required", "downstream CMake package metadata")
    if expect_directml and lower_name in {"directml.dll", "directml.debug.dll"}:
        return InventoryEntry(relative, file_size(path), "required", "DirectML runtime DLL")
    if suffix == ".pdb":
        return InventoryEntry(relative, file_size(path), "removable", "debug symbols are not needed to link or run")
    return InventoryEntry(relative, file_size(path), "optional", "packaged support file")


def remove_release_pdbs(root: Path, buildtype: str) -> List[str]:
    if buildtype.lower() != "release":
        return []
    removed = []
    for path in relative_files(root):
        if path.suffix.lower() == ".pdb":
            removed.append(relative_name(root, path))
            path.unlink()
    return removed


def validate_required_layout(root: Path, buildtype: str, expect_directml: bool) -> Path:
    primary_library = find_primary_library(root, buildtype)

    headers = find_headers(root)
    if not headers:
        raise WindowsArtifactError("Required public headers are missing under onnxruntime/include")

    cmake_files = find_cmake_package_files(root)
    if not cmake_files:
        raise WindowsArtifactError(
            "Required CMake package files are missing under onnxruntime/lib/cmake/onnxruntime"
        )

    if expect_directml and not find_directml_dlls(root):
        raise WindowsArtifactError("DirectML runtime DLL is missing from onnxruntime/bin")

    return primary_library


def build_inventory(root: Path, buildtype: str, expect_directml: bool) -> dict:
    files = relative_files(root)
    primary_library = validate_required_layout(root, buildtype, expect_directml)
    entries = [
        classify_file(root, path, primary_library, expect_directml)
        for path in files
    ]
    largest = sorted(entries, key=lambda entry: entry.size, reverse=True)[:20]

    return {
        "buildtype": buildtype,
        "file_count": len(files),
        "total_bytes": sum(file_size(path) for path in files),
        "top_level": top_level_inventory(root, files),
        "areas": {
            "onnxruntime/lib": size_by_predicate(
                files,
                lambda path: relative_name(root, path).startswith("onnxruntime/lib/"),
            ),
            "onnxruntime/bin": size_by_predicate(
                files,
                lambda path: relative_name(root, path).startswith("onnxruntime/bin/"),
            ),
            ".lib": size_by_predicate(files, lambda path: path.suffix.lower() == ".lib"),
            ".dll": size_by_predicate(files, lambda path: path.suffix.lower() == ".dll"),
            ".pdb": size_by_predicate(files, lambda path: path.suffix.lower() == ".pdb"),
            "cmake_metadata": size_by_predicate(
                files,
                lambda path: relative_name(root, path).startswith(
                    "onnxruntime/lib/cmake/onnxruntime/"
                )
                and path.suffix.lower() == ".cmake",
            ),
        },
        "largest_files": [asdict(entry) for entry in largest],
        "classification": [asdict(entry) for entry in entries],
    }


def print_summary(inventory: dict, removed_pdbs: List[str]) -> None:
    print(f"Windows artifact build type: {inventory['buildtype']}")
    print(f"Files: {inventory['file_count']}")
    print(f"Total staged bytes: {inventory['total_bytes']}")
    print("Area inventory:")
    for name, entry in inventory["areas"].items():
        print(f"  {name}: {entry['files']} files, {entry['bytes']} bytes")
    if removed_pdbs:
        print("Removed Release PDB files:")
        for path in removed_pdbs:
            print(f"  {path}")
    else:
        print("Removed Release PDB files: none")
    print("Largest staged files:")
    for entry in inventory["largest_files"][:10]:
        print(
            f"  {entry['size']} bytes {entry['classification']} "
            f"{entry['path']} ({entry['reason']})"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("build/artifact"),
        help="Staged artifact root containing the onnxruntime directory.",
    )
    parser.add_argument(
        "--buildtype",
        choices=("Debug", "Release"),
        required=True,
        help="Build type being packaged.",
    )
    parser.add_argument(
        "--expect-directml",
        action="store_true",
        help="Require DirectML runtime DLLs under onnxruntime/bin.",
    )
    parser.add_argument(
        "--inventory-output",
        type=Path,
        help="Optional JSON file for the post-slim inventory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.artifact_root
    if not root.is_dir():
        raise WindowsArtifactError(f"Artifact root does not exist: {root}")

    before_inventory = build_inventory(root, args.buildtype, args.expect_directml)
    removed_pdbs = remove_release_pdbs(root, args.buildtype)
    after_inventory = build_inventory(root, args.buildtype, args.expect_directml)
    after_inventory["removed_pdbs"] = removed_pdbs
    after_inventory["baseline_total_bytes"] = before_inventory["total_bytes"]
    after_inventory["slimmed_total_bytes"] = after_inventory["total_bytes"]

    if args.inventory_output:
        args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_output.write_text(
            json.dumps(after_inventory, indent=2) + "\n",
            encoding="utf-8",
        )

    print_summary(after_inventory, removed_pdbs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
