#!/usr/bin/env python3
"""Tests for resolve_build_targets.py."""

from __future__ import annotations

import unittest

from resolve_build_targets import TargetResolutionError, resolve_targets


class ResolveBuildTargetsTest(unittest.TestCase):
    def test_target_all_includes_universal_targets_and_source_slices(self) -> None:
        resolution = resolve_targets("all")

        self.assertIn("macos-aarch64-static", resolution.build_target_names)
        self.assertIn("macos-x86_64-static", resolution.build_target_names)
        self.assertIn("ios-simulator-aarch64-static", resolution.build_target_names)
        self.assertIn("ios-simulator-x86_64-static", resolution.build_target_names)
        self.assertEqual(
            resolution.universal_target_names,
            ["macos-universal-static", "ios-simulator-universal-static"],
        )
        self.assertEqual(resolution.xcframework_target_names, ["apple-xcframework"])

    def test_macos_universal_selected_alone_schedules_sources(self) -> None:
        resolution = resolve_targets("macos-universal-static")

        self.assertEqual(
            resolution.build_target_names,
            ["macos-aarch64-static", "macos-x86_64-static"],
        )
        self.assertEqual(resolution.universal_target_names, ["macos-universal-static"])

    def test_ios_simulator_universal_selected_alone_schedules_sources(self) -> None:
        resolution = resolve_targets("ios-simulator-universal-static")

        self.assertEqual(
            resolution.build_target_names,
            ["ios-simulator-aarch64-static", "ios-simulator-x86_64-static"],
        )
        self.assertEqual(
            resolution.universal_target_names,
            ["ios-simulator-universal-static"],
        )
        self.assertEqual(resolution.xcframework_target_names, [])

    def test_apple_xcframework_selected_alone_schedules_sources(self) -> None:
        resolution = resolve_targets("apple-xcframework")

        self.assertEqual(
            resolution.build_target_names,
            [
                "ios-aarch64-static",
                "ios-simulator-aarch64-static",
                "ios-simulator-x86_64-static",
                "macos-aarch64-static",
                "macos-x86_64-static",
            ],
        )
        self.assertEqual(
            resolution.universal_target_names,
            ["ios-simulator-universal-static", "macos-universal-static"],
        )
        self.assertEqual(resolution.xcframework_target_names, ["apple-xcframework"])

    def test_source_slices_without_universal_do_not_package_universal(self) -> None:
        resolution = resolve_targets("macos-aarch64-static,macos-x86_64-static")

        self.assertEqual(
            resolution.build_target_names,
            ["macos-aarch64-static", "macos-x86_64-static"],
        )
        self.assertEqual(resolution.universal_target_names, [])
        self.assertEqual(resolution.xcframework_target_names, [])

    def test_single_architecture_selection_stays_single_architecture(self) -> None:
        resolution = resolve_targets("ios-simulator-aarch64-static")

        self.assertEqual(resolution.build_target_names, ["ios-simulator-aarch64-static"])
        self.assertEqual(resolution.universal_target_names, [])
        self.assertEqual(resolution.xcframework_target_names, [])

    def test_release_buildtype_is_default_matrix_buildtype(self) -> None:
        resolution = resolve_targets("linux-x86_64-static")

        self.assertEqual(
            [target["buildtype"] for target in resolution.build_targets],
            ["Release"],
        )

    def test_both_buildtype_expands_each_matrix(self) -> None:
        resolution = resolve_targets(
            "apple-xcframework",
            raw_buildtype="Both",
        )

        self.assertEqual(
            [target["buildtype"] for target in resolution.build_targets],
            ["Debug"] * 5 + ["Release"] * 5,
        )
        self.assertEqual(
            [target["buildtype"] for target in resolution.universal_targets],
            ["Debug", "Debug", "Release", "Release"],
        )
        self.assertEqual(
            [target["buildtype"] for target in resolution.xcframework_targets],
            ["Debug", "Release"],
        )
        self.assertEqual(
            resolution.build_target_names,
            [
                "ios-aarch64-static",
                "ios-simulator-aarch64-static",
                "ios-simulator-x86_64-static",
                "macos-aarch64-static",
                "macos-x86_64-static",
            ],
        )

    def test_unknown_buildtype_fails(self) -> None:
        with self.assertRaisesRegex(TargetResolutionError, "Unknown build type"):
            resolve_targets("linux-x86_64-static", raw_buildtype="Profile")

    def test_unknown_target_fails(self) -> None:
        with self.assertRaisesRegex(TargetResolutionError, "Unknown build target"):
            resolve_targets("macos-arm64-static")

    def test_universal_missing_prerequisites_can_fail_validation(self) -> None:
        with self.assertRaisesRegex(TargetResolutionError, "requires source target"):
            resolve_targets(
                "macos-universal-static",
                include_universal_prerequisites=False,
            )


if __name__ == "__main__":
    unittest.main()
