#!/usr/bin/env python3
"""Tests for validate_public_headers.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATE_SCRIPT = SCRIPT_DIR / "validate_public_headers.py"

COMMON_HEADERS = {
    "cpu_provider_factory.h",
    "onnxruntime_c_api.h",
    "onnxruntime_cxx_api.h",
    "onnxruntime_cxx_inline.h",
    "onnxruntime_float16.h",
    "onnxruntime_lite_custom_op.h",
    "onnxruntime_run_options_config_keys.h",
    "onnxruntime_session_options_config_keys.h",
}


def write_headers(root: Path, headers: set[str], raw_header: bool = False) -> None:
    include_root = root / "onnxruntime" / "include" / "onnxruntime"
    include_root.mkdir(parents=True)
    for header in headers:
        (include_root / header).write_text("#pragma once\n", encoding="utf-8")
    if raw_header:
        raw_path = include_root / "core" / "session" / "onnxruntime_c_api.h"
        raw_path.parent.mkdir(parents=True)
        raw_path.write_text("#pragma once\n", encoding="utf-8")


class ValidatePublicHeadersTest(unittest.TestCase):
    def run_script(
        self,
        root: Path,
        target: str,
        build_args: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATE_SCRIPT),
                "--artifact-root",
                str(root),
                "--target",
                target,
                "--build-args",
                build_args,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_ios_coreml_headers_match_exact_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-ios-headers-") as temp:
            root = Path(temp)
            headers = set(COMMON_HEADERS)
            headers.add("coreml_provider_factory.h")
            write_headers(root, headers)

            result = self.run_script(root, "ios-aarch64-static", "--static --coreml -N")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("coreml_provider_factory.h", result.stdout)

    def test_android_nnapi_headers_match_exact_set(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-android-headers-") as temp:
            root = Path(temp)
            headers = set(COMMON_HEADERS)
            headers.add("nnapi_provider_factory.h")
            write_headers(root, headers)

            result = self.run_script(
                root,
                "android-arm64-v8a-static",
                "--static --android --nnapi -N",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("nnapi_provider_factory.h", result.stdout)

    def test_android_missing_nnapi_header_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-android-missing-nnapi-") as temp:
            root = Path(temp)
            write_headers(root, set(COMMON_HEADERS))

            result = self.run_script(
                root,
                "android-arm64-v8a-static",
                "--static --android --nnapi -N",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nnapi_provider_factory.h", result.stderr)

    def test_raw_nested_header_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-raw-headers-") as temp:
            root = Path(temp)
            headers = set(COMMON_HEADERS)
            headers.add("nnapi_provider_factory.h")
            write_headers(root, headers, raw_header=True)

            result = self.run_script(
                root,
                "android-arm64-v8a-static",
                "--static --android --nnapi -N",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nested raw source directories", result.stderr)
            self.assertIn("core", result.stderr)

    def test_non_mobile_target_allows_extra_root_headers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-linux-headers-") as temp:
            root = Path(temp)
            headers = set(COMMON_HEADERS)
            headers.update({"openvino_provider_factory.h", "provider_options.h"})
            write_headers(root, headers)

            result = self.run_script(
                root,
                "linux-x86_64-static",
                "--static --xnnpack --openvino -N",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("openvino_provider_factory.h", result.stdout)


if __name__ == "__main__":
    unittest.main()
