#!/usr/bin/env python3
"""Functional tests for Apple XCFramework artifact packaging."""

from __future__ import annotations

import json
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CREATE_SCRIPT = SCRIPT_DIR / "create_apple_xcframework_artifact.py"
MANIFEST_SCRIPT = SCRIPT_DIR / "generate_manifest.py"


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def sdk_path(sdk: str) -> str | None:
    result = subprocess.run(
        ["xcrun", "--sdk", sdk, "--show-sdk-path"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def compile_static_library(
    work_dir: Path,
    name: str,
    platform_name: str,
    arch: str,
) -> Path:
    source = work_dir / f"{name}-{arch}.c"
    source.write_text(
        "#include \"onnxruntime_c_api.h\"\n"
        "const OrtApiBase* OrtGetApiBase(void) {\n"
        "  static OrtApiBase api_base = {0};\n"
        "  return &api_base;\n"
        "}\n",
        encoding="utf-8",
    )

    object_file = work_dir / f"{name}-{arch}.o"
    archive = work_dir / f"{name}-{arch}.a"
    include_dir = write_headers(work_dir / "compile-headers")

    if platform_name == "macos":
        command = [
            "clang",
            "-arch",
            arch,
            "-mmacosx-version-min=13.3",
            "-I",
            str(include_dir),
            "-c",
            str(source),
            "-o",
            str(object_file),
        ]
    elif platform_name == "ios":
        iphoneos_sdk = sdk_path("iphoneos")
        if not iphoneos_sdk:
            raise unittest.SkipTest("iPhoneOS SDK is unavailable")
        command = [
            "clang",
            "-target",
            "arm64-apple-ios15.0",
            "-isysroot",
            iphoneos_sdk,
            "-I",
            str(include_dir),
            "-c",
            str(source),
            "-o",
            str(object_file),
        ]
    elif platform_name == "ios-simulator":
        simulator_sdk = sdk_path("iphonesimulator")
        if not simulator_sdk:
            raise unittest.SkipTest("iPhone Simulator SDK is unavailable")
        target = {
            "arm64": "arm64-apple-ios15.0-simulator",
            "x86_64": "x86_64-apple-ios15.0-simulator",
        }[arch]
        command = [
            "clang",
            "-target",
            target,
            "-isysroot",
            simulator_sdk,
            "-I",
            str(include_dir),
            "-c",
            str(source),
            "-o",
            str(object_file),
        ]
    else:
        raise AssertionError(f"Unsupported fixture platform: {platform_name}")

    run(command)
    run(["libtool", "-static", "-o", str(archive), str(object_file)])
    return archive


def write_headers(root: Path, header_suffix: str = "") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "onnxruntime_c_api.h").write_text(
        "#pragma once\n"
        "#ifdef __cplusplus\n"
        "extern \"C\" {\n"
        "#endif\n"
        "typedef struct OrtApiBase { int fixture; } OrtApiBase;\n"
        "const OrtApiBase* OrtGetApiBase(void);\n"
        "#ifdef __cplusplus\n"
        "}\n"
        "#endif\n"
        f"{header_suffix}\n",
        encoding="utf-8",
    )
    (root / "onnxruntime_cxx_api.h").write_text(
        "#pragma once\n"
        "#include \"onnxruntime_c_api.h\"\n"
        "namespace Ort { inline const OrtApiBase* GetApiBase() { return OrtGetApiBase(); } }\n",
        encoding="utf-8",
    )
    return root


def lipo_create(output: Path, libraries: list[Path]) -> Path:
    run(["lipo", "-create", *[str(library) for library in libraries], "-output", str(output)])
    return output


def write_source_artifact(
    archive_path: Path,
    library_path: Path,
    header_suffix: str = "",
    reduced_ops_value: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
) -> None:
    root = archive_path.parent / f"{archive_path.stem}-root"
    include_dir = root / "onnxruntime" / "include"
    lib_dir = root / "onnxruntime" / "lib"
    include_dir.mkdir(parents=True)
    lib_dir.mkdir(parents=True)
    write_headers(include_dir, header_suffix=header_suffix)
    (root / "onnxruntime" / "reduced_operators.json").write_text(
        json.dumps(
            {
                "reduced_ops": True,
                "required_operators_config_sha256": reduced_ops_value,
                "required_operators_config_sha256_short": reduced_ops_value[:12],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.copy2(library_path, lib_dir / "libonnxruntime.a")

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zip_file.write(path, path.relative_to(root).as_posix())


@unittest.skipUnless(platform.system() == "Darwin", "Apple XCFramework fixtures require macOS")
@unittest.skipUnless(command_available("xcodebuild"), "xcodebuild is unavailable")
@unittest.skipUnless(command_available("xcrun"), "xcrun is unavailable")
@unittest.skipUnless(command_available("lipo"), "lipo is unavailable")
@unittest.skipUnless(command_available("clang"), "clang is unavailable")
@unittest.skipUnless(command_available("libtool"), "libtool is unavailable")
class CreateAppleXCFrameworkArtifactTest(unittest.TestCase):
    def build_source_archives(self, temp_dir: Path) -> tuple[Path, Path, Path]:
        ios_device_library = compile_static_library(
            temp_dir,
            "ios-device",
            "ios",
            "arm64",
        )
        ios_simulator_library = lipo_create(
            temp_dir / "ios-simulator-universal.a",
            [
                compile_static_library(temp_dir, "ios-simulator", "ios-simulator", "arm64"),
                compile_static_library(temp_dir, "ios-simulator", "ios-simulator", "x86_64"),
            ],
        )
        macos_library = lipo_create(
            temp_dir / "macos-universal.a",
            [
                compile_static_library(temp_dir, "macos", "macos", "arm64"),
                compile_static_library(temp_dir, "macos", "macos", "x86_64"),
            ],
        )

        ios_device_archive = temp_dir / "ort-v1.22.2-ios-aarch64-static-release.zip"
        ios_simulator_archive = temp_dir / "ort-v1.22.2-ios-simulator-universal-static-release.zip"
        macos_archive = temp_dir / "ort-v1.22.2-macos-universal-static-release.zip"
        write_source_artifact(ios_device_archive, ios_device_library)
        write_source_artifact(ios_simulator_archive, ios_simulator_library)
        write_source_artifact(macos_archive, macos_library)
        return ios_device_archive, ios_simulator_archive, macos_archive

    def run_packager(
        self,
        temp_dir: Path,
        ios_device_archive: Path,
        ios_simulator_archive: Path,
        macos_archive: Path,
    ) -> Path:
        output_archive = temp_dir / "ort-v1.22.2-apple-xcframework-ops-0123456789ab-release.zip"
        result = run(
            [
                sys.executable,
                str(CREATE_SCRIPT),
                "--ios-device-archive",
                str(ios_device_archive),
                "--ios-simulator-archive",
                str(ios_simulator_archive),
                "--macos-archive",
                str(macos_archive),
                "--output-archive",
                str(output_archive),
            ]
        )
        self.assertIn("arm64", result.stdout)
        self.assertIn("x86_64", result.stdout)
        return output_archive

    def assert_xcframework_archive(self, archive: Path) -> None:
        extract_dir = archive.parent / f"{archive.stem}-extract"
        with zipfile.ZipFile(archive, "r") as zip_file:
            names = zip_file.namelist()
            self.assertIn("onnxruntime.xcframework/Info.plist", names)
            self.assertIn("README.md", names)
            zip_file.extractall(extract_dir)

        info_path = extract_dir / "onnxruntime.xcframework" / "Info.plist"
        with info_path.open("rb") as handle:
            info = plistlib.load(handle)

        libraries = info["AvailableLibraries"]
        platforms = {
            (entry["SupportedPlatform"], entry.get("SupportedPlatformVariant"))
            for entry in libraries
        }
        self.assertIn(("ios", None), platforms)
        self.assertIn(("ios", "simulator"), platforms)
        self.assertIn(("macos", None), platforms)

        for entry in libraries:
            identifier = entry["LibraryIdentifier"]
            slice_root = extract_dir / "onnxruntime.xcframework" / identifier
            self.assertTrue((slice_root / entry["LibraryPath"]).is_file())
            self.assertTrue((slice_root / entry.get("HeadersPath", "Headers")).is_dir())

    def test_xcframework_archive_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-apple-xcframework-") as temp:
            temp_dir = Path(temp)
            archives = self.build_source_archives(temp_dir)
            output_archive = self.run_packager(temp_dir, *archives)

            self.assert_xcframework_archive(output_archive)

            manifest_artifact_dir = temp_dir / "artifacts" / output_archive.stem
            manifest_artifact_dir.mkdir(parents=True)
            shutil.copy2(output_archive, manifest_artifact_dir / output_archive.name)
            run([sys.executable, str(MANIFEST_SCRIPT)], cwd=temp_dir)
            manifest = json.loads((temp_dir / "manifest.json").read_text(encoding="utf-8"))

            key = "apple-xcframework-ops-0123456789ab-release"
            self.assertIn(key, manifest)
            self.assertEqual(manifest[key]["artifact_type"], "apple-xcframework")
            self.assertEqual(manifest[key]["xcframework"], "onnxruntime.xcframework")
            self.assertEqual(len(manifest[key]["libraries"]), 3)
            self.assertTrue(manifest[key]["reduced_ops"])

    def test_header_mismatch_fails_before_packaging(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-apple-xcframework-mismatch-") as temp:
            temp_dir = Path(temp)
            ios_device_archive, ios_simulator_archive, _ = self.build_source_archives(temp_dir)
            macos_library = lipo_create(
                temp_dir / "macos-mismatch-universal.a",
                [
                    compile_static_library(temp_dir, "macos-mismatch", "macos", "arm64"),
                    compile_static_library(temp_dir, "macos-mismatch", "macos", "x86_64"),
                ],
            )
            macos_archive = temp_dir / "macos-mismatch.zip"
            write_source_artifact(macos_archive, macos_library, header_suffix="#define DIFFERENT 1")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_SCRIPT),
                    "--ios-device-archive",
                    str(ios_device_archive),
                    "--ios-simulator-archive",
                    str(ios_simulator_archive),
                    "--macos-archive",
                    str(macos_archive),
                    "--output-archive",
                    str(temp_dir / "out.zip"),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Public header content differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
