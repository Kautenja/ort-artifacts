#!/usr/bin/env python3
"""Validate Android static ONNX Runtime artifacts for API-24 consumers."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


TARGET_ABIS = {
    "android-arm64-v8a-static": "arm64-v8a",
    "android-armeabi-v7a-static": "armeabi-v7a",
    "android-x86_64-static": "x86_64",
    "android-x86-static": "x86",
}

TLS_RELOCATION_PATTERN = re.compile(r"\bR_(?:AARCH64|ARM|X86_64|386)_[A-Z0-9_]*TLS[A-Z0-9_]*\b")


class AndroidArchiveError(ValueError):
    """An Android archive validation error that is safe to print in CI logs."""


def abi_for_target(target: str) -> str:
    try:
        return TARGET_ABIS[target]
    except KeyError as exc:
        supported = ", ".join(sorted(TARGET_ABIS))
        raise AndroidArchiveError(
            f"Unsupported Android static target '{target}'. Supported targets: {supported}."
        ) from exc


def package_root(artifact_root: Path) -> Path:
    root = artifact_root / "onnxruntime"
    if not root.is_dir():
        raise AndroidArchiveError(f"ONNX Runtime package root is missing: {root}")
    return root


def static_archive_path(artifact_root: Path) -> Path:
    lib_dir = package_root(artifact_root) / "lib"
    if not lib_dir.is_dir():
        raise AndroidArchiveError(f"ONNX Runtime lib directory is missing: {lib_dir}")

    preferred = lib_dir / "libonnxruntime.a"
    if preferred.is_file():
        return preferred

    candidates = sorted(lib_dir.glob("libonnxruntime*.a"))
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        raise AndroidArchiveError(
            "Multiple ONNX Runtime static archives were found: "
            + ", ".join(path.name for path in candidates)
        )
    raise AndroidArchiveError(f"ONNX Runtime static archive is missing under {lib_dir}")


def cmake_package_dir(artifact_root: Path) -> Path:
    config_dir = package_root(artifact_root) / "lib" / "cmake" / "onnxruntime"
    if not (config_dir / "onnxruntimeConfig.cmake").is_file():
        raise AndroidArchiveError(f"ONNX Runtime CMake package is missing: {config_dir}")
    return config_dir


def first_existing_tool(names: Sequence[str]) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise AndroidArchiveError(f"Required tool was not found on PATH: one of {', '.join(names)}")


def ndk_tool(ndk_home: Path | None, tool_name: str) -> str | None:
    if ndk_home is not None:
        for candidate in sorted((ndk_home / "toolchains" / "llvm" / "prebuilt").glob("*/bin")):
            path = candidate / tool_name
            if path.is_file():
                return str(path)
            exe_path = candidate / f"{tool_name}.exe"
            if exe_path.is_file():
                return str(exe_path)
    return shutil.which(tool_name)


def command_output(command: Sequence[str]) -> str:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        raise AndroidArchiveError(
            "Command failed while inspecting archive: "
            + " ".join(command)
            + "\n"
            + result.stdout
        )
    return result.stdout


def archive_symbol_output(archive: Path, ndk_home: Path | None) -> str:
    nm = ndk_tool(ndk_home, "llvm-nm") or ndk_tool(ndk_home, "nm")
    if nm is None:
        raise AndroidArchiveError("Neither llvm-nm nor nm was found for archive inspection.")
    return command_output([nm, "-A", "--undefined-only", str(archive)])


def archive_relocation_output(archive: Path, ndk_home: Path | None) -> str:
    readelf = ndk_tool(ndk_home, "llvm-readelf") or ndk_tool(ndk_home, "readelf")
    if readelf is None:
        raise AndroidArchiveError("Neither llvm-readelf nor readelf was found for archive inspection.")
    return command_output([readelf, "--relocs", str(archive)])


def offending_tls_relocations(relocation_output: str) -> list[str]:
    lines = []
    for line in relocation_output.splitlines():
        if TLS_RELOCATION_PATTERN.search(line) and "__emutls_" not in line:
            lines.append(line.strip())
    return lines


def inspect_tls_compatibility(archive: Path, android_api: int, ndk_home: Path | None) -> list[str]:
    symbol_output = archive_symbol_output(archive, ndk_home)
    relocation_output = archive_relocation_output(archive, ndk_home)

    combined_output = symbol_output + "\n" + relocation_output

    if android_api < 29 and "__tls_get_addr" in combined_output:
        raise AndroidArchiveError(
            f"{archive} exposes __tls_get_addr, which requires Android API 29 ELF TLS."
        )

    tls_relocations = offending_tls_relocations(relocation_output)
    if android_api < 29 and tls_relocations:
        preview = "\n".join(tls_relocations[:10])
        raise AndroidArchiveError(
            f"{archive} contains ELF TLS relocations that are not valid for Android API {android_api}:\n"
            + preview
        )

    notes = []
    if "__emutls_" in combined_output:
        notes.append("Detected __emutls_* references, which are allowed for pre-29 Android.")
    return notes


def write_smoke_project(source_dir: Path) -> None:
    (source_dir / "CMakeLists.txt").write_text(
        "\n".join(
            [
                "cmake_minimum_required(VERSION 3.22)",
                "project(ort_android_static_smoke LANGUAGES C CXX)",
                "find_package(onnxruntime REQUIRED CONFIG)",
                "add_library(ort_static_smoke SHARED smoke.cc)",
                "target_link_libraries(ort_static_smoke PRIVATE onnxruntime::onnxruntime)",
                'target_link_options(ort_static_smoke PRIVATE "-Wl,--no-undefined")',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (source_dir / "smoke.cc").write_text(
        "\n".join(
            [
                "#include <onnxruntime/onnxruntime_c_api.h>",
                "",
                "extern \"C\" int ort_android_static_smoke(void) {",
                "  return OrtGetApiBase() == nullptr;",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def smoke_configure_command(
    *,
    cmake: str,
    source_dir: Path,
    build_dir: Path,
    ndk_home: Path,
    abi: str,
    android_api: int,
    package_dir: Path,
) -> list[str]:
    return [
        cmake,
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={ndk_home / 'build' / 'cmake' / 'android.toolchain.cmake'}",
        f"-DANDROID_ABI={abi}",
        f"-DANDROID_PLATFORM=android-{android_api}",
        f"-Donnxruntime_DIR={package_dir}",
        "-DCMAKE_BUILD_TYPE=Release",
    ]


def smoke_build_command(*, cmake: str, build_dir: Path) -> list[str]:
    return [cmake, "--build", str(build_dir), "--verbose"]


def run_command(command: Sequence[str]) -> None:
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise AndroidArchiveError("Command failed: " + " ".join(command))


def run_link_smoke_test(artifact_root: Path, target: str, android_api: int, ndk_home: Path) -> None:
    abi = abi_for_target(target)
    toolchain = ndk_home / "build" / "cmake" / "android.toolchain.cmake"
    if not toolchain.is_file():
        raise AndroidArchiveError(f"Android NDK CMake toolchain is missing: {toolchain}")

    package_dir = cmake_package_dir(artifact_root)
    cmake = first_existing_tool(["cmake"])

    with tempfile.TemporaryDirectory(prefix="ort-android-static-smoke-") as temp:
        temp_dir = Path(temp)
        source_dir = temp_dir / "src"
        build_dir = temp_dir / "build"
        source_dir.mkdir()
        write_smoke_project(source_dir)

        run_command(
            smoke_configure_command(
                cmake=cmake,
                source_dir=source_dir,
                build_dir=build_dir,
                ndk_home=ndk_home,
                abi=abi,
                android_api=android_api,
                package_dir=package_dir,
            )
        )
        run_command(smoke_build_command(cmake=cmake, build_dir=build_dir))


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
        help="Android build target name, such as android-arm64-v8a-static.",
    )
    parser.add_argument(
        "--android-api",
        type=int,
        default=24,
        help="Android API level to validate against.",
    )
    parser.add_argument(
        "--ndk-home",
        type=Path,
        default=None,
        help="Android NDK root. Defaults to ANDROID_NDK_HOME.",
    )
    parser.add_argument(
        "--skip-smoke-test",
        action="store_true",
        help="Only inspect archive symbols/relocations; intended for unit tests.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        abi = abi_for_target(args.target)
        archive = static_archive_path(args.artifact_root)
        ndk_home = args.ndk_home
        if ndk_home is None:
            raw_env = os.environ.get("ANDROID_NDK_HOME")
            ndk_home = Path(raw_env) if raw_env else None

        notes = inspect_tls_compatibility(archive, args.android_api, ndk_home)

        if not args.skip_smoke_test:
            if ndk_home is None:
                raise AndroidArchiveError(
                    "ANDROID_NDK_HOME must be set, or --ndk-home must be supplied, for the link smoke test."
                )
            run_link_smoke_test(args.artifact_root, args.target, args.android_api, ndk_home)
    except AndroidArchiveError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    print(
        f"Validated Android static archive for {args.target} "
        f"({abi}, android-{args.android_api}): {archive}"
    )
    for note in notes:
        print(f"  {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
