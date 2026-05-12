#!/usr/bin/env python3
"""Create an Apple XCFramework ONNX Runtime artifact from source static zips."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


PRIMARY_STATIC_LIBRARIES = (
    "onnxruntime/lib/libonnxruntime.a",
    "onnxruntime/lib/libonnxruntimed.a",
)
REDUCED_OPS_METADATA = "onnxruntime/reduced_operators.json"
REQUIRED_PUBLIC_HEADERS = (
    "onnxruntime_c_api.h",
    "onnxruntime_cxx_api.h",
)
MACOS_DEPLOYMENT_TARGET = "13.3"
IOS_DEPLOYMENT_TARGET = "15.0"
APPLE_LINK_FLAGS = (
    "-lc++",
    "-framework",
    "Foundation",
    "-framework",
    "CoreML",
    "-framework",
    "Accelerate",
    "-pthread",
)


class XCFrameworkArtifactError(ValueError):
    """A packaging error that is safe to show in GitHub Actions logs."""


@dataclass(frozen=True)
class SourceArtifact:
    label: str
    archive: Path
    root: Path
    library: Path
    headers: Path


@dataclass(frozen=True)
class XCFrameworkLibrary:
    identifier: str
    platform: str
    variant: str | None
    library: Path
    headers: Path
    architectures: Sequence[str]


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
                    raise XCFrameworkArtifactError(
                        f"Archive {archive} contains an unsafe path: {member.filename}"
                    )
                zip_file.extract(member, destination)
    except zipfile.BadZipFile as exc:
        raise XCFrameworkArtifactError(f"Source artifact is not a zip archive: {archive}") from exc


def find_primary_library(root: Path) -> Path:
    candidates = [
        root / relative_path
        for relative_path in PRIMARY_STATIC_LIBRARIES
        if (root / relative_path).is_file()
    ]
    if len(candidates) != 1:
        raise XCFrameworkArtifactError(
            "Expected exactly one ONNX Runtime static library under onnxruntime/lib; "
            f"found {len(candidates)}."
        )
    return candidates[0]


def find_header(headers: Path, filename: str) -> Path:
    matches = sorted(headers.rglob(filename), key=lambda path: len(path.relative_to(headers).parts))
    if not matches:
        raise XCFrameworkArtifactError(
            f"Public headers do not include required ONNX Runtime header: {filename}"
        )
    return matches[0]


def extract_source_artifact(label: str, archive: Path, destination: Path) -> SourceArtifact:
    if not archive.is_file():
        raise XCFrameworkArtifactError(f"Required {label} source artifact was not found: {archive}")

    safe_extract_zip(archive, destination)
    library = find_primary_library(destination)
    headers = destination / "onnxruntime" / "include"
    if not headers.is_dir():
        raise XCFrameworkArtifactError(f"{label} source artifact does not contain onnxruntime/include.")
    for required_header in REQUIRED_PUBLIC_HEADERS:
        find_header(headers, required_header)

    return SourceArtifact(
        label=label,
        archive=archive,
        root=destination,
        library=library,
        headers=headers,
    )


def header_files(source: SourceArtifact) -> List[str]:
    files = [
        path.relative_to(source.root).as_posix()
        for path in source.headers.rglob("*")
        if path.is_file()
    ]
    if not files:
        raise XCFrameworkArtifactError(f"{source.label} source artifact does not contain public headers.")
    return sorted(files)


def compare_headers(sources: Sequence[SourceArtifact]) -> None:
    first = sources[0]
    first_headers = header_files(first)
    for source in sources[1:]:
        source_headers = header_files(source)
        if source_headers != first_headers:
            raise XCFrameworkArtifactError(
                "Public header trees differ between source artifacts: "
                f"{first.label} vs {source.label}"
            )
        for relative_path in first_headers:
            if file_sha256(first.root / relative_path) != file_sha256(source.root / relative_path):
                raise XCFrameworkArtifactError(
                    "Public header content differs between source artifacts: "
                    f"{relative_path}"
                )


def compare_reduced_ops_metadata(sources: Sequence[SourceArtifact]) -> None:
    first_metadata = sources[0].root / REDUCED_OPS_METADATA
    for source in sources[1:]:
        metadata = source.root / REDUCED_OPS_METADATA
        if first_metadata.exists() != metadata.exists():
            raise XCFrameworkArtifactError(
                "Reduced-operator metadata is not present in every Apple source artifact."
            )
        if first_metadata.exists() and file_sha256(first_metadata) != file_sha256(metadata):
            raise XCFrameworkArtifactError(
                "Reduced-operator metadata differs between Apple source artifacts."
            )


def run_capture(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def command_output(result: subprocess.CompletedProcess[str]) -> str:
    return "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)


def fail_command(description: str, command: Sequence[str], result: subprocess.CompletedProcess[str]) -> None:
    raise XCFrameworkArtifactError(
        f"{description} failed with exit code {result.returncode}: {' '.join(command)}\n"
        f"{command_output(result)}"
    )


def run_required(command: Sequence[str], description: str) -> subprocess.CompletedProcess[str]:
    result = run_capture(command)
    if result.returncode != 0:
        fail_command(description, command, result)
    return result


def sdk_path(xcrun: str, sdk: str) -> str:
    result = run_capture([xcrun, "--sdk", sdk, "--show-sdk-path"])
    if result.returncode != 0 or not result.stdout.strip():
        fail_command(f"SDK discovery for {sdk}", [xcrun, "--sdk", sdk, "--show-sdk-path"], result)
    return result.stdout.strip()


def verify_lipo(lipo: str, label: str, library: Path, expected_arches: Sequence[str]) -> str:
    verify_command = [lipo, str(library), "-verify_arch", *expected_arches]
    verify_result = run_capture(verify_command)
    if verify_result.returncode != 0:
        fail_command(
            f"{label} static library architecture verification",
            verify_command,
            verify_result,
        )

    info_result = run_required([lipo, "-info", str(library)], f"{label} lipo -info")
    return info_result.stdout.strip()


def create_xcframework(
    xcodebuild: str,
    ios_device: SourceArtifact,
    ios_simulator: SourceArtifact,
    macos: SourceArtifact,
    output_xcframework: Path,
) -> None:
    if output_xcframework.exists():
        shutil.rmtree(output_xcframework)

    command = [
        xcodebuild,
        "-create-xcframework",
        "-library",
        str(ios_device.library),
        "-headers",
        str(ios_device.headers),
        "-library",
        str(ios_simulator.library),
        "-headers",
        str(ios_simulator.headers),
        "-library",
        str(macos.library),
        "-headers",
        str(macos.headers),
        "-output",
        str(output_xcframework),
    ]
    run_required(command, "xcodebuild -create-xcframework")


def read_xcframework_libraries(xcframework: Path) -> List[XCFrameworkLibrary]:
    info_path = xcframework / "Info.plist"
    if not info_path.is_file():
        raise XCFrameworkArtifactError("Generated XCFramework does not contain Info.plist.")

    with info_path.open("rb") as handle:
        info = plistlib.load(handle)

    libraries = []
    for entry in info.get("AvailableLibraries", []):
        identifier = entry["LibraryIdentifier"]
        slice_root = xcframework / identifier
        headers_path = entry.get("HeadersPath", "Headers")
        libraries.append(
            XCFrameworkLibrary(
                identifier=identifier,
                platform=entry["SupportedPlatform"],
                variant=entry.get("SupportedPlatformVariant"),
                library=slice_root / entry["LibraryPath"],
                headers=slice_root / headers_path,
                architectures=tuple(entry.get("SupportedArchitectures", [])),
            )
        )
    if not libraries:
        raise XCFrameworkArtifactError("Generated XCFramework does not list any libraries.")
    return libraries


def require_xcframework_library(
    libraries: Sequence[XCFrameworkLibrary],
    platform_name: str,
    variant: str | None,
) -> XCFrameworkLibrary:
    matches = [
        library
        for library in libraries
        if library.platform == platform_name and library.variant == variant
    ]
    if len(matches) != 1:
        variant_label = variant or "device"
        raise XCFrameworkArtifactError(
            f"Expected exactly one XCFramework library for {platform_name} {variant_label}; "
            f"found {len(matches)}."
        )
    library = matches[0]
    if not library.library.is_file():
        raise XCFrameworkArtifactError(
            f"XCFramework slice {library.identifier} does not contain {library.library.name}."
        )
    if not library.headers.is_dir():
        raise XCFrameworkArtifactError(
            f"XCFramework slice {library.identifier} does not contain packaged headers."
        )
    for required_header in REQUIRED_PUBLIC_HEADERS:
        find_header(library.headers, required_header)
    return library


def header_include(headers: Path, filename: str) -> str:
    return find_header(headers, filename).relative_to(headers).as_posix()


def host_apple_arch(supported_arches: Sequence[str]) -> str:
    host = platform.machine().lower()
    preferred = "arm64" if host in {"arm64", "aarch64"} else "x86_64"
    if preferred in supported_arches:
        return preferred
    if supported_arches:
        return supported_arches[0]
    return preferred


def classify_smoke_failure(output: str) -> str:
    lower = output.lower()
    if "building for" in lower and "but linking in object file built for" in lower:
        return "incompatible platform or deployment target"
    if "undefined symbols" in lower or "symbol(s) not found" in lower:
        return "missing Apple framework/library linker settings or incomplete static library content"
    if "file not found" in lower or "no such file" in lower:
        return "bad packaged headers or missing SDK/system include paths"
    if "sdk" in lower and ("not found" in lower or "unavailable" in lower):
        return "missing Apple SDK"
    return "consumer build settings or static-library content"


def run_consumer_smoke(
    label: str,
    command: Sequence[str],
    source: Path,
) -> None:
    result = run_capture(command)
    if result.returncode == 0:
        return

    output = command_output(result)
    category = classify_smoke_failure(output)
    raise XCFrameworkArtifactError(
        f"{label} consumer compile/link smoke test failed ({category}).\n"
        f"Source: {source}\n"
        f"Command: {' '.join(command)}\n"
        f"{output}"
    )


def write_consumer_source(path: Path, headers: Path) -> None:
    c_api = header_include(headers, "onnxruntime_c_api.h")
    cxx_api = header_include(headers, "onnxruntime_cxx_api.h")
    path.write_text(
        f"#include <{c_api}>\n"
        f"#include <{cxx_api}>\n"
        "\n"
        "int main() {\n"
        "  const OrtApiBase* api_base = OrtGetApiBase();\n"
        "  return api_base == nullptr;\n"
        "}\n",
        encoding="utf-8",
    )


def run_smoke_tests(
    xcrun: str,
    macos_library: XCFrameworkLibrary,
    ios_simulator_library: XCFrameworkLibrary,
    work_dir: Path,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    macos_sdk = sdk_path(xcrun, "macosx")
    simulator_sdk = sdk_path(xcrun, "iphonesimulator")

    macos_arch = host_apple_arch(macos_library.architectures)
    macos_source = work_dir / "macos-consumer.cc"
    write_consumer_source(macos_source, macos_library.headers)
    macos_command = [
        "clang++",
        "-std=c++17",
        "-arch",
        macos_arch,
        "-isysroot",
        macos_sdk,
        f"-mmacosx-version-min={MACOS_DEPLOYMENT_TARGET}",
        "-I",
        str(macos_library.headers),
        str(macos_source),
        str(macos_library.library),
        *APPLE_LINK_FLAGS,
        "-o",
        str(work_dir / "macos-consumer"),
    ]
    run_consumer_smoke("macOS", macos_command, macos_source)

    simulator_arch = host_apple_arch(ios_simulator_library.architectures)
    simulator_source = work_dir / "ios-simulator-consumer.cc"
    write_consumer_source(simulator_source, ios_simulator_library.headers)
    simulator_command = [
        "clang++",
        "-std=c++17",
        "-target",
        f"{simulator_arch}-apple-ios{IOS_DEPLOYMENT_TARGET}-simulator",
        "-isysroot",
        simulator_sdk,
        f"-mios-simulator-version-min={IOS_DEPLOYMENT_TARGET}",
        "-I",
        str(ios_simulator_library.headers),
        str(simulator_source),
        str(ios_simulator_library.library),
        *APPLE_LINK_FLAGS,
        "-o",
        str(work_dir / "ios-simulator-consumer"),
    ]
    run_consumer_smoke("iOS simulator", simulator_command, simulator_source)


def write_readme(package_root: Path) -> None:
    (package_root / "README.md").write_text(
        "# ONNX Runtime Apple XCFramework\n"
        "\n"
        "This archive contains `onnxruntime.xcframework` for iOS device arm64, "
        "iOS simulator arm64/x86_64, and macOS arm64/x86_64.\n"
        "\n"
        "## Xcode Link Settings\n"
        "\n"
        "- Add `onnxruntime.xcframework` to Frameworks, Libraries, and Embedded Content.\n"
        "- Link `Foundation.framework`, `CoreML.framework`, and `Accelerate.framework`.\n"
        "- Add `-lc++` to Other Linker Flags.\n"
        "- Use deployment targets at least iOS 15.0 and macOS 13.3.\n"
        "\n"
        "The packaging workflow validates SDK discovery with `xcrun`, verifies source "
        "architectures with `lipo`, creates the bundle with `xcodebuild -create-xcframework`, "
        "and compiles/links minimal macOS and iOS simulator consumers before uploading.\n",
        encoding="utf-8",
    )


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


def create_xcframework_artifact(
    ios_device_archive: Path,
    ios_simulator_archive: Path,
    macos_archive: Path,
    output_archive: Path,
    lipo: str = "lipo",
    xcodebuild: str = "xcodebuild",
    xcrun: str = "xcrun",
) -> List[str]:
    with tempfile.TemporaryDirectory(prefix="apple-xcframework-") as temp:
        workspace = Path(temp)
        ios_device = extract_source_artifact(
            "iOS device",
            ios_device_archive,
            workspace / "ios-device",
        )
        ios_simulator = extract_source_artifact(
            "iOS simulator universal",
            ios_simulator_archive,
            workspace / "ios-simulator",
        )
        macos = extract_source_artifact(
            "macOS universal",
            macos_archive,
            workspace / "macos",
        )

        sources = (ios_device, ios_simulator, macos)
        compare_headers(sources)
        compare_reduced_ops_metadata(sources)

        lipo_info = [
            verify_lipo(lipo, "iOS device", ios_device.library, ("arm64",)),
            verify_lipo(lipo, "iOS simulator universal", ios_simulator.library, ("arm64", "x86_64")),
            verify_lipo(lipo, "macOS universal", macos.library, ("arm64", "x86_64")),
        ]

        output_xcframework = workspace / "onnxruntime.xcframework"
        create_xcframework(
            xcodebuild=xcodebuild,
            ios_device=ios_device,
            ios_simulator=ios_simulator,
            macos=macos,
            output_xcframework=output_xcframework,
        )

        libraries = read_xcframework_libraries(output_xcframework)
        require_xcframework_library(libraries, "ios", None)
        ios_simulator_library = require_xcframework_library(libraries, "ios", "simulator")
        macos_library = require_xcframework_library(libraries, "macos", None)
        run_smoke_tests(
            xcrun=xcrun,
            macos_library=macos_library,
            ios_simulator_library=ios_simulator_library,
            work_dir=workspace / "smoke",
        )

        package_root = workspace / "package"
        package_root.mkdir()
        shutil.copytree(output_xcframework, package_root / "onnxruntime.xcframework")
        write_readme(package_root)
        write_zip_from_directory(package_root, output_archive)

    return lipo_info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ios-device-archive", required=True, type=Path)
    parser.add_argument("--ios-simulator-archive", required=True, type=Path)
    parser.add_argument("--macos-archive", required=True, type=Path)
    parser.add_argument("--output-archive", required=True, type=Path)
    parser.add_argument("--lipo", default="lipo")
    parser.add_argument("--xcodebuild", default="xcodebuild")
    parser.add_argument("--xcrun", default="xcrun")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        lipo_info = create_xcframework_artifact(
            ios_device_archive=args.ios_device_archive,
            ios_simulator_archive=args.ios_simulator_archive,
            macos_archive=args.macos_archive,
            output_archive=args.output_archive,
            lipo=args.lipo,
            xcodebuild=args.xcodebuild,
            xcrun=args.xcrun,
        )
    except XCFrameworkArtifactError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    for info in lipo_info:
        print(info)
    print(f"Created {args.output_archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
