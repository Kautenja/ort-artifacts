#!/usr/bin/env python3
"""Tests for validate_android_static_archive.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validate_android_static_archive import (
    AndroidArchiveError,
    abi_for_target,
    inspect_tls_compatibility,
    smoke_configure_command,
    static_archive_path,
)


class ValidateAndroidStaticArchiveTest(unittest.TestCase):
    def test_allows_emulated_tls_for_api24(self) -> None:
        with patch(
            "validate_android_static_archive.archive_symbol_output",
            return_value="lib.a(member.o): U __emutls_get_address\n",
        ), patch(
            "validate_android_static_archive.archive_relocation_output",
            return_value="",
        ):
            notes = inspect_tls_compatibility(Path("libonnxruntime.a"), 24, None)

        self.assertEqual(
            notes,
            ["Detected __emutls_* references, which are allowed for pre-29 Android."],
        )

    def test_rejects_tls_get_addr_for_api24(self) -> None:
        with patch(
            "validate_android_static_archive.archive_symbol_output",
            return_value="lib.a(member.o): U __tls_get_addr\n",
        ), patch(
            "validate_android_static_archive.archive_relocation_output",
            return_value="",
        ):
            with self.assertRaisesRegex(AndroidArchiveError, "__tls_get_addr"):
                inspect_tls_compatibility(Path("libonnxruntime.a"), 24, None)

    def test_rejects_elf_tls_relocations_for_api24(self) -> None:
        relocation_output = """
Relocation section '.rela.text' at offset 0x0 contains 1 entry:
000000000000  000000000000 R_AARCH64_TLS_DTPMOD64  __tls_object + 0
"""
        with patch(
            "validate_android_static_archive.archive_symbol_output",
            return_value="",
        ), patch(
            "validate_android_static_archive.archive_relocation_output",
            return_value=relocation_output,
        ):
            with self.assertRaisesRegex(AndroidArchiveError, "ELF TLS relocations"):
                inspect_tls_compatibility(Path("libonnxruntime.a"), 24, None)

    def test_missing_static_archive_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ort-missing-lib-") as temp:
            lib_dir = Path(temp) / "onnxruntime" / "lib"
            lib_dir.mkdir(parents=True)

            with self.assertRaisesRegex(AndroidArchiveError, "static archive is missing"):
                static_archive_path(Path(temp))

    def test_unsupported_abi_target_fails(self) -> None:
        with self.assertRaisesRegex(AndroidArchiveError, "Unsupported Android static target"):
            abi_for_target("android-mips-static")

    def test_smoke_configure_command_uses_api24_and_target_abi(self) -> None:
        command = smoke_configure_command(
            cmake="cmake",
            source_dir=Path("/tmp/src"),
            build_dir=Path("/tmp/build"),
            ndk_home=Path("/ndk"),
            abi="x86",
            android_api=24,
            package_dir=Path("/artifact/onnxruntime/lib/cmake/onnxruntime"),
        )

        self.assertIn("-DANDROID_ABI=x86", command)
        self.assertIn("-DANDROID_PLATFORM=android-24", command)
        self.assertIn(
            "-DCMAKE_TOOLCHAIN_FILE=/ndk/build/cmake/android.toolchain.cmake",
            command,
        )
        self.assertIn(
            "-Donnxruntime_DIR=/artifact/onnxruntime/lib/cmake/onnxruntime",
            command,
        )


if __name__ == "__main__":
    unittest.main()
