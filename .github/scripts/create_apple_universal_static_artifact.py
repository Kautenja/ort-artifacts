#!/usr/bin/env python3
"""Create an Apple universal static ONNX Runtime artifact from two source zips."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


PRIMARY_STATIC_LIBRARIES = (
    "onnxruntime/lib/libonnxruntime.a",
    "onnxruntime/lib/libonnxruntimed.a",
)
REDUCED_OPS_METADATA = "onnxruntime/reduced_operators.json"
HEADER_PREFIX = "onnxruntime/include/"


class UniversalArtifactError(ValueError):
    """A packaging error that is safe to show in GitHub Actions logs."""


@dataclass(frozen=True)
class UniversalTarget:
    target: str
    expected_arches: Sequence[str]


UNIVERSAL_TARGETS = {
    "macos-universal-static": UniversalTarget(
        target="macos-universal-static",
        expected_arches=("arm64", "x86_64"),
    ),
    "ios-simulator-universal-static": UniversalTarget(
        target="ios-simulator-universal-static",
        expected_arches=("arm64", "x86_64"),
    ),
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    try:
        with zipfile.ZipFile(archive, "r") as zip_file:
            for member in zip_file.infolist():
                target = (destination / member.filename).resolve()
                if os.path.commonpath([root, target]) != str(root):
                    raise UniversalArtifactError(
                        f"Archive {archive} contains an unsafe path: {member.filename}"
                    )
                zip_file.extract(member, destination)
    except zipfile.BadZipFile as exc:
        raise UniversalArtifactError(f"Source artifact is not a zip archive: {archive}") from exc


def relative_files(root: Path) -> List[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )


def find_primary_library(root: Path) -> str:
    candidates = [
        relative_path
        for relative_path in PRIMARY_STATIC_LIBRARIES
        if (root / relative_path).is_file()
    ]
    if len(candidates) != 1:
        raise UniversalArtifactError(
            "Expected exactly one ONNX Runtime static library under onnxruntime/lib; "
            f"found {len(candidates)}."
        )
    return candidates[0]


def compare_file_sets(first: Path, second: Path, ignored: Iterable[str]) -> None:
    ignored_set = set(ignored)
    first_files = {
        relative_path
        for relative_path in relative_files(first)
        if relative_path not in ignored_set
    }
    second_files = {
        relative_path
        for relative_path in relative_files(second)
        if relative_path not in ignored_set
    }

    only_first = sorted(first_files - second_files)
    only_second = sorted(second_files - first_files)
    if only_first or only_second:
        details = []
        if only_first:
            details.append(f"only in aarch64 source: {', '.join(only_first[:5])}")
        if only_second:
            details.append(f"only in x86_64 source: {', '.join(only_second[:5])}")
        raise UniversalArtifactError(
            "Source artifact layouts differ after excluding the primary static library: "
            + "; ".join(details)
        )


def compare_headers(first: Path, second: Path) -> None:
    first_headers = [
        relative_path
        for relative_path in relative_files(first)
        if relative_path.startswith(HEADER_PREFIX)
    ]
    second_headers = [
        relative_path
        for relative_path in relative_files(second)
        if relative_path.startswith(HEADER_PREFIX)
    ]

    if not first_headers:
        raise UniversalArtifactError("Source artifact does not contain public headers.")
    if first_headers != second_headers:
        raise UniversalArtifactError("Public header trees differ between source artifacts.")

    for relative_path in first_headers:
        if file_sha256(first / relative_path) != file_sha256(second / relative_path):
            raise UniversalArtifactError(
                f"Public header content differs between source artifacts: {relative_path}"
            )


def compare_reduced_ops_metadata(first: Path, second: Path) -> None:
    first_metadata = first / REDUCED_OPS_METADATA
    second_metadata = second / REDUCED_OPS_METADATA

    if first_metadata.exists() != second_metadata.exists():
        raise UniversalArtifactError(
            "Reduced-operator metadata is present in only one source artifact."
        )
    if first_metadata.exists() and file_sha256(first_metadata) != file_sha256(second_metadata):
        raise UniversalArtifactError(
            "Reduced-operator metadata differs between source artifacts."
        )


def compare_matching_metadata(first: Path, second: Path, ignored: Iterable[str]) -> None:
    ignored_set = set(ignored)
    for relative_path in relative_files(first):
        if relative_path in ignored_set:
            continue
        if file_sha256(first / relative_path) != file_sha256(second / relative_path):
            raise UniversalArtifactError(
                f"Source artifact metadata differs between architectures: {relative_path}"
            )


def run_checked(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def create_universal_library(
    lipo: str,
    aarch64_library: Path,
    x86_64_library: Path,
    output_library: Path,
    expected_arches: Sequence[str],
) -> str:
    output_library.parent.mkdir(parents=True, exist_ok=True)
    create_result = run_checked(
        [
            lipo,
            "-create",
            str(aarch64_library),
            str(x86_64_library),
            "-output",
            str(output_library),
        ]
    )
    if create_result.returncode != 0:
        raise UniversalArtifactError(
            "lipo -create failed: "
            + (create_result.stderr.strip() or create_result.stdout.strip())
        )

    verify_result = run_checked(
        [lipo, str(output_library), "-verify_arch", *expected_arches]
    )
    if verify_result.returncode != 0:
        raise UniversalArtifactError(
            "Universal library is missing an expected architecture: "
            + (verify_result.stderr.strip() or verify_result.stdout.strip())
        )

    info_result = run_checked([lipo, "-info", str(output_library)])
    if info_result.returncode != 0:
        raise UniversalArtifactError(
            "lipo -info failed: "
            + (info_result.stderr.strip() or info_result.stdout.strip())
        )
    return info_result.stdout.strip()


def write_zip_from_directory(root: Path, output_archive: Path) -> None:
    output_archive.parent.mkdir(parents=True, exist_ok=True)
    if output_archive.exists():
        output_archive.unlink()

    with zipfile.ZipFile(
        output_archive,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zip_file.write(path, path.relative_to(root).as_posix())


def create_universal_artifact(
    target: str,
    aarch64_archive: Path,
    x86_64_archive: Path,
    output_archive: Path,
    lipo: str = "lipo",
) -> str:
    if target not in UNIVERSAL_TARGETS:
        raise UniversalArtifactError(
            f"Unsupported universal Apple target '{target}'. "
            f"Expected one of: {', '.join(UNIVERSAL_TARGETS)}."
        )
    if not aarch64_archive.is_file():
        raise UniversalArtifactError(
            f"Required aarch64 source artifact archive was not found: {aarch64_archive}"
        )
    if not x86_64_archive.is_file():
        raise UniversalArtifactError(
            f"Required x86_64 source artifact archive was not found: {x86_64_archive}"
        )

    target_config = UNIVERSAL_TARGETS[target]
    with tempfile.TemporaryDirectory(prefix=f"{target}-") as temp_dir:
        workspace = Path(temp_dir)
        aarch64_root = workspace / "aarch64"
        x86_64_root = workspace / "x86_64"
        output_root = workspace / "output"

        safe_extract_zip(aarch64_archive, aarch64_root)
        safe_extract_zip(x86_64_archive, x86_64_root)
        shutil.copytree(aarch64_root, output_root)

        aarch64_library = find_primary_library(aarch64_root)
        x86_64_library = find_primary_library(x86_64_root)
        if aarch64_library != x86_64_library:
            raise UniversalArtifactError(
                "Source artifacts use different primary static library names: "
                f"{aarch64_library} vs {x86_64_library}"
            )

        compare_file_sets(aarch64_root, x86_64_root, ignored=[aarch64_library])
        compare_headers(aarch64_root, x86_64_root)
        compare_reduced_ops_metadata(aarch64_root, x86_64_root)
        compare_matching_metadata(aarch64_root, x86_64_root, ignored=[aarch64_library])

        universal_library = workspace / "libonnxruntime-universal.a"
        info = create_universal_library(
            lipo=lipo,
            aarch64_library=aarch64_root / aarch64_library,
            x86_64_library=x86_64_root / x86_64_library,
            output_library=universal_library,
            expected_arches=target_config.expected_arches,
        )

        output_library = output_root / aarch64_library
        output_library.unlink()
        shutil.move(str(universal_library), output_library)
        write_zip_from_directory(output_root, output_archive)

    return info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(UNIVERSAL_TARGETS))
    parser.add_argument("--aarch64-archive", required=True, type=Path)
    parser.add_argument("--x86_64-archive", required=True, type=Path)
    parser.add_argument("--output-archive", required=True, type=Path)
    parser.add_argument("--lipo", default="lipo")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        info = create_universal_artifact(
            target=args.target,
            aarch64_archive=args.aarch64_archive,
            x86_64_archive=args.x86_64_archive,
            output_archive=args.output_archive,
            lipo=args.lipo,
        )
    except UniversalArtifactError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    print(info)
    print(f"Created {args.output_archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
