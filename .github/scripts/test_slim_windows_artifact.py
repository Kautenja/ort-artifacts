#!/usr/bin/env python3
"""Tests for slim_windows_artifact.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SLIM_SCRIPT = SCRIPT_DIR / "slim_windows_artifact.py"


def write_file(path: Path, size: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def create_artifact(root: Path, buildtype: str = "Release", directml: bool = True) -> None:
    lib_name = "onnxruntimed.lib" if buildtype == "Debug" else "onnxruntime.lib"
    write_file(root / "onnxruntime" / "lib" / lib_name, 64)
    write_file(root / "onnxruntime" / "include" / "onnxruntime" / "onnxruntime_c_api.h", 16)
    write_file(root / "onnxruntime" / "lib" / "cmake" / "onnxruntime" / "onnxruntimeConfig.cmake", 8)
    write_file(root / "onnxruntime" / "lib" / "cmake" / "onnxruntime" / "onnxruntimeTargets.cmake", 8)
    if directml:
        dll_name = "DirectML.Debug.dll" if buildtype == "Debug" else "DirectML.dll"
        write_file(root / "onnxruntime" / "bin" / dll_name, 32)


class SlimWindowsArtifactTest(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SLIM_SCRIPT), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_release_removes_pdb_and_keeps_required_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-windows-release-") as temp:
            root = Path(temp)
            create_artifact(root, "Release")
            write_file(root / "onnxruntime" / "bin" / "DirectML.pdb", 128)
            inventory = root / "inventory.json"

            result = self.run_script(
                "--artifact-root",
                str(root),
                "--buildtype",
                "Release",
                "--expect-directml",
                "--inventory-output",
                str(inventory),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "onnxruntime" / "bin" / "DirectML.pdb").exists())
            self.assertTrue((root / "onnxruntime" / "bin" / "DirectML.dll").is_file())
            self.assertTrue((root / "onnxruntime" / "lib" / "onnxruntime.lib").is_file())
            self.assertTrue(inventory.is_file())
            payload = json.loads(inventory.read_text(encoding="utf-8"))
            self.assertEqual(payload["removed_pdbs"], ["onnxruntime/bin/DirectML.pdb"])
            self.assertLess(payload["slimmed_total_bytes"], payload["baseline_total_bytes"])

    def test_debug_preserves_pdb(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-windows-debug-") as temp:
            root = Path(temp)
            create_artifact(root, "Debug")
            write_file(root / "onnxruntime" / "bin" / "DirectML.Debug.pdb", 128)

            result = self.run_script(
                "--artifact-root",
                str(root),
                "--buildtype",
                "Debug",
                "--expect-directml",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "onnxruntime" / "bin" / "DirectML.Debug.pdb").is_file())

    def test_directml_runtime_is_required_when_expected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-windows-missing-dml-") as temp:
            root = Path(temp)
            create_artifact(root, "Release", directml=False)

            result = self.run_script(
                "--artifact-root",
                str(root),
                "--buildtype",
                "Release",
                "--expect-directml",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DirectML runtime DLL is missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
