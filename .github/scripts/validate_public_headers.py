#!/usr/bin/env python3
"""Validate the public ONNX Runtime header layout in a staged artifact."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Iterable


COMMON_PUBLIC_HEADERS = {
    "cpu_provider_factory.h",
    "onnxruntime_c_api.h",
    "onnxruntime_cxx_api.h",
    "onnxruntime_cxx_inline.h",
    "onnxruntime_float16.h",
    "onnxruntime_lite_custom_op.h",
    "onnxruntime_run_options_config_keys.h",
    "onnxruntime_session_options_config_keys.h",
}

PROVIDER_HEADERS = {
    "--coreml": "coreml_provider_factory.h",
    "--nnapi": "nnapi_provider_factory.h",
    "--directml": "dml_provider_factory.h",
    "--openvino": "openvino_provider_factory.h",
}


class PublicHeaderError(ValueError):
    """A packaging error that is safe to print in GitHub Actions logs."""


def parse_build_args(raw_args: str) -> set[str]:
    if not raw_args:
        return set()
    return set(shlex.split(raw_args))


def expected_headers(build_args: Iterable[str]) -> set[str]:
    args = set(build_args)
    headers = set(COMMON_PUBLIC_HEADERS)
    for build_arg, header in PROVIDER_HEADERS.items():
        if build_arg in args:
            headers.add(header)
    return headers


def public_header_root(artifact_root: Path) -> Path:
    return artifact_root / "onnxruntime" / "include" / "onnxruntime"


def root_headers(include_root: Path) -> set[str]:
    return {
        path.name
        for path in include_root.iterdir()
        if path.is_file() and path.suffix.lower() in {".h", ".hpp"}
    }


def nested_entries(include_root: Path) -> list[str]:
    return sorted(
        path.relative_to(include_root).as_posix()
        for path in include_root.rglob("*")
        if path.is_dir()
    )


def target_requires_exact_headers(target: str) -> bool:
    return target.startswith("ios-") or target.startswith("android-")


def validate_public_headers(artifact_root: Path, target: str, build_args: str) -> list[str]:
    include_root = public_header_root(artifact_root)
    if not include_root.is_dir():
        raise PublicHeaderError(f"Public header root is missing: {include_root}")

    nested = nested_entries(include_root)
    if nested:
        raise PublicHeaderError(
            "Public header root contains nested raw source directories: "
            + ", ".join(nested[:10])
        )

    expected = expected_headers(parse_build_args(build_args))
    actual = root_headers(include_root)
    missing = sorted(expected - actual)
    if missing:
        raise PublicHeaderError(
            "Public header root is missing required headers: " + ", ".join(missing)
        )

    if target_requires_exact_headers(target):
        extra = sorted(actual - expected)
        if extra:
            raise PublicHeaderError(
                f"{target} public header root contains unexpected headers: "
                + ", ".join(extra)
            )

    return sorted(actual)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path("build/artifact"),
        help="Staged artifact root containing the onnxruntime directory.",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Build target name, such as ios-aarch64-static or android-arm64-v8a-static.",
    )
    parser.add_argument(
        "--build-args",
        default="",
        help="Resolved build.sh arguments for the target.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        headers = validate_public_headers(args.artifact_root, args.target, args.build_args)
    except PublicHeaderError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    print(f"Validated public headers for {args.target}:")
    for header in headers:
        print(f"  {header}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
