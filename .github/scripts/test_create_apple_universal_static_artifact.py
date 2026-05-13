#!/usr/bin/env python3
"""Functional tests for Apple universal static artifact packaging."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CREATE_SCRIPT = SCRIPT_DIR / "create_apple_universal_static_artifact.py"
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


def simulator_sdk_path() -> str | None:
    result = subprocess.run(
        ["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"],
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
    arch: str,
    platform_name: str,
) -> Path:
    source = work_dir / f"{platform_name}-{arch}.c"
    source.write_text(
        "int ort_artifacts_universal_fixture(void) { return 42; }\n",
        encoding="utf-8",
    )

    object_file = work_dir / f"{platform_name}-{arch}.o"
    archive = work_dir / f"{platform_name}-{arch}.a"

    if platform_name == "macos":
        run(
            [
                "clang",
                "-arch",
                arch,
                "-mmacosx-version-min=13.3",
                "-c",
                str(source),
                "-o",
                str(object_file),
            ]
        )
    elif platform_name == "ios-simulator":
        sdk_path = simulator_sdk_path()
        if not sdk_path:
            raise unittest.SkipTest("iPhone Simulator SDK is unavailable")
        target = {
            "arm64": "arm64-apple-ios15.0-simulator",
            "x86_64": "x86_64-apple-ios15.0-simulator",
        }[arch]
        run(
            [
                "clang",
                "-target",
                target,
                "-isysroot",
                sdk_path,
                "-c",
                str(source),
                "-o",
                str(object_file),
            ]
        )
    else:
        raise AssertionError(f"Unsupported platform fixture: {platform_name}")

    run(["libtool", "-static", "-o", str(archive), str(object_file)])
    return archive


def write_source_artifact(
    archive_path: Path,
    library_path: Path,
    header_value: str = "same",
    reduced_ops_value: str = "same",
) -> None:
    root = archive_path.parent / f"{archive_path.stem}-root"
    include_dir = root / "onnxruntime" / "include" / "onnxruntime"
    lib_dir = root / "onnxruntime" / "lib"
    include_dir.mkdir(parents=True)
    lib_dir.mkdir(parents=True)
    (include_dir / "fixture.h").write_text(
        f"#pragma once\n#define ORT_FIXTURE_{header_value.upper()} 1\n",
        encoding="utf-8",
    )
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


@unittest.skipUnless(platform.system() == "Darwin", "Apple lipo fixtures require macOS")
@unittest.skipUnless(command_available("lipo"), "lipo is unavailable")
@unittest.skipUnless(command_available("clang"), "clang is unavailable")
@unittest.skipUnless(command_available("libtool"), "libtool is unavailable")
class CreateAppleUniversalStaticArtifactTest(unittest.TestCase):
    def build_source_archives(
        self,
        temp_dir: Path,
        platform_name: str,
    ) -> tuple[Path, Path]:
        arm64_library = compile_static_library(temp_dir, "arm64", platform_name)
        x86_64_library = compile_static_library(temp_dir, "x86_64", platform_name)

        arm64_archive = temp_dir / f"{platform_name}-aarch64.zip"
        x86_64_archive = temp_dir / f"{platform_name}-x86_64.zip"
        write_source_artifact(
            arm64_archive,
            arm64_library,
            reduced_ops_value="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        )
        write_source_artifact(
            x86_64_archive,
            x86_64_library,
            reduced_ops_value="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        )
        return arm64_archive, x86_64_archive

    def run_packager(
        self,
        temp_dir: Path,
        target: str,
        arm64_archive: Path,
        x86_64_archive: Path,
        output_name: str,
    ) -> Path:
        output_archive = temp_dir / output_name
        result = run(
            [
                sys.executable,
                str(CREATE_SCRIPT),
                "--target",
                target,
                "--aarch64-archive",
                str(arm64_archive),
                "--x86_64-archive",
                str(x86_64_archive),
                "--output-archive",
                str(output_archive),
            ]
        )
        self.assertIn("arm64", result.stdout)
        self.assertIn("x86_64", result.stdout)
        return output_archive

    def assert_universal_archive(self, archive: Path) -> None:
        extract_dir = archive.parent / f"{archive.stem}-extract"
        with zipfile.ZipFile(archive, "r") as zip_file:
            names = zip_file.namelist()
            self.assertIn("onnxruntime/lib/libonnxruntime.a", names)
            self.assertIn("onnxruntime/include/onnxruntime/fixture.h", names)
            self.assertIn("onnxruntime/reduced_operators.json", names)
            zip_file.extractall(extract_dir)

        info = run(["lipo", "-info", str(extract_dir / "onnxruntime/lib/libonnxruntime.a")])
        self.assertIn("arm64", info.stdout)
        self.assertIn("x86_64", info.stdout)

    def test_macos_universal_archive_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-macos-universal-") as temp:
            temp_dir = Path(temp)
            arm64_archive, x86_64_archive = self.build_source_archives(temp_dir, "macos")
            output_archive = self.run_packager(
                temp_dir,
                "macos-universal-static",
                arm64_archive,
                x86_64_archive,
                "ort-v1.22.2-macos-universal-static-ops-0123456789ab-release.zip",
            )

            self.assert_universal_archive(output_archive)

            manifest_artifact_dir = (
                temp_dir
                / "artifacts"
                / "ort-v1.22.2-macos-universal-static-ops-0123456789ab-release"
            )
            manifest_artifact_dir.mkdir(parents=True)
            shutil.copy2(output_archive, manifest_artifact_dir / output_archive.name)
            arch_artifact = "ort-v1.22.2-macos-aarch64-static-release"
            arch_artifact_dir = temp_dir / "artifacts" / arch_artifact
            arch_artifact_dir.mkdir(parents=True)
            shutil.copy2(arm64_archive, arch_artifact_dir / f"{arch_artifact}.zip")
            run([sys.executable, str(MANIFEST_SCRIPT)], cwd=temp_dir)
            manifest = json.loads((temp_dir / "manifest.json").read_text(encoding="utf-8"))

            key = "macos-universal-static-ops-0123456789ab-release"
            self.assertIn(key, manifest)
            self.assertEqual(manifest[key]["artifact"], output_archive.stem)
            self.assertEqual(manifest[key]["lib_dir"], "onnxruntime/lib")
            self.assertEqual(manifest[key]["ort_lib"], "onnxruntime/lib/libonnxruntime.a")
            self.assertTrue(manifest[key]["reduced_ops"])
            self.assertIn("macos-aarch64-static-release", manifest)
            self.assertEqual(
                manifest["macos-aarch64-static-release"]["archive"],
                f"{arch_artifact}.zip",
            )
            self.assertEqual(
                manifest["macos-aarch64-static-release"]["ort_lib"],
                "onnxruntime/lib/libonnxruntime.a",
            )

    def test_ios_simulator_universal_archive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-ios-simulator-universal-") as temp:
            temp_dir = Path(temp)
            arm64_archive, x86_64_archive = self.build_source_archives(
                temp_dir,
                "ios-simulator",
            )
            output_archive = self.run_packager(
                temp_dir,
                "ios-simulator-universal-static",
                arm64_archive,
                x86_64_archive,
                "ort-v1.22.2-ios-simulator-universal-static-release.zip",
            )

            self.assert_universal_archive(output_archive)

    def test_header_mismatch_fails_before_packaging(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-universal-header-mismatch-") as temp:
            temp_dir = Path(temp)
            arm64_library = compile_static_library(temp_dir, "arm64", "macos")
            x86_64_library = compile_static_library(temp_dir, "x86_64", "macos")
            arm64_archive = temp_dir / "arm64.zip"
            x86_64_archive = temp_dir / "x86_64.zip"
            write_source_artifact(arm64_archive, arm64_library, header_value="one")
            write_source_artifact(x86_64_archive, x86_64_library, header_value="two")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_SCRIPT),
                    "--target",
                    "macos-universal-static",
                    "--aarch64-archive",
                    str(arm64_archive),
                    "--x86_64-archive",
                    str(x86_64_archive),
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

    def test_reduced_ops_mismatch_fails_before_packaging(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-universal-reduced-mismatch-") as temp:
            temp_dir = Path(temp)
            arm64_library = compile_static_library(temp_dir, "arm64", "macos")
            x86_64_library = compile_static_library(temp_dir, "x86_64", "macos")
            arm64_archive = temp_dir / "arm64.zip"
            x86_64_archive = temp_dir / "x86_64.zip"
            write_source_artifact(
                arm64_archive,
                arm64_library,
                reduced_ops_value="aaaaaaaaaaaa0000000000000000000000000000000000000000000000000000",
            )
            write_source_artifact(
                x86_64_archive,
                x86_64_library,
                reduced_ops_value="bbbbbbbbbbbb0000000000000000000000000000000000000000000000000000",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(CREATE_SCRIPT),
                    "--target",
                    "macos-universal-static",
                    "--aarch64-archive",
                    str(arm64_archive),
                    "--x86_64-archive",
                    str(x86_64_archive),
                    "--output-archive",
                    str(temp_dir / "out.zip"),
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Reduced-operator metadata differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
