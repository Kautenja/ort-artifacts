#!/usr/bin/env python3
"""Resolve workflow target checkboxes into build and derived target matrices."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


class TargetResolutionError(ValueError):
    """A target selection error that is safe to show in GitHub Actions logs."""


@dataclass(frozen=True)
class BuildTarget:
    target: str
    args: str
    runs_on: str
    providers: Sequence[str]

    def matrix_entry(self, provider_inputs: Dict[str, bool]) -> Dict[str, object]:
        disabled_provider_flags = {
            PROVIDER_FLAGS[provider]
            for provider in self.providers
            if not provider_inputs[provider]
        }
        args = [
            token
            for token in shlex.split(self.args)
            if token not in disabled_provider_flags
        ]
        enabled_providers = [
            provider
            for provider in self.providers
            if provider_inputs[provider]
        ]
        return {
            "target": self.target,
            "args": " ".join(args),
            "runs-on": self.runs_on,
            "providers": list(self.providers),
            "enabled-providers": enabled_providers,
        }


@dataclass(frozen=True)
class UniversalTarget:
    target: str
    source_aarch64_target: str
    source_x86_64_target: str

    @property
    def source_targets(self) -> Sequence[str]:
        return (self.source_aarch64_target, self.source_x86_64_target)

    def matrix_entry(self) -> Dict[str, str]:
        return {
            "target": self.target,
            "source_aarch64_target": self.source_aarch64_target,
            "source_x86_64_target": self.source_x86_64_target,
        }


@dataclass(frozen=True)
class Resolution:
    build_targets: List[Dict[str, object]]
    universal_targets: List[Dict[str, str]]
    notices: List[str]

    @property
    def build_target_names(self) -> List[str]:
        return [str(target["target"]) for target in self.build_targets]

    @property
    def universal_target_names(self) -> List[str]:
        return [target["target"] for target in self.universal_targets]

    def output_values(self) -> Dict[str, str]:
        return {
            "matrix": json.dumps({"include": self.build_targets}, separators=(",", ":")),
            "targets": ",".join(self.build_target_names),
            "universal_matrix": json.dumps(
                {"include": self.universal_targets},
                separators=(",", ":"),
            ),
            "universal_targets": ",".join(self.universal_target_names),
        }


PROVIDER_FLAGS = {
    "xnnpack": "--xnnpack",
    "openvino": "--openvino",
    "directml": "--directml",
    "coreml": "--coreml",
    "nnapi": "--nnapi",
}

PROVIDER_LABELS = {
    "xnnpack": "XNNPACK",
    "openvino": "OpenVINO",
    "directml": "DirectML",
    "coreml": "CoreML",
    "nnapi": "NNAPI",
}

DEFAULT_PROVIDER_INPUTS = {
    "xnnpack": True,
    "openvino": True,
    "directml": True,
    "coreml": True,
    "nnapi": True,
}

BUILD_TARGETS = [
    BuildTarget(
        target="linux-aarch64-static",
        args="--static -A aarch64 --xnnpack -N --openvino",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "openvino"),
    ),
    BuildTarget(
        target="linux-x86_64-static",
        args="--static --xnnpack -N --openvino",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "openvino"),
    ),
    BuildTarget(
        target="macos-aarch64-static",
        args="--static -A aarch64 --xnnpack --coreml -N",
        runs_on="macos-14",
        providers=("xnnpack", "coreml"),
    ),
    BuildTarget(
        target="macos-x86_64-static",
        args="--static --xnnpack --coreml -N",
        runs_on="macos-14",
        providers=("xnnpack", "coreml"),
    ),
    BuildTarget(
        target="windows-md-x86_64-static",
        args="--static --directml --xnnpack -N",
        runs_on="windows-2022",
        providers=("directml", "xnnpack"),
    ),
    BuildTarget(
        target="ios-aarch64-static",
        args="--static --iphoneos -A aarch64 --xnnpack --coreml -N",
        runs_on="macos-14",
        providers=("xnnpack", "coreml"),
    ),
    BuildTarget(
        target="ios-simulator-aarch64-static",
        args="--static --iphonesimulator -A aarch64 --xnnpack --coreml -N",
        runs_on="macos-14",
        providers=("xnnpack", "coreml"),
    ),
    BuildTarget(
        target="ios-simulator-x86_64-static",
        args="--static --iphonesimulator -A x86_64 --xnnpack --coreml -N",
        runs_on="macos-14",
        providers=("xnnpack", "coreml"),
    ),
    BuildTarget(
        target="android-arm64-v8a-static",
        args="--static --android --android_abi arm64-v8a --xnnpack --nnapi -N",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "nnapi"),
    ),
    BuildTarget(
        target="android-armeabi-v7a-static",
        args="--static --android --android_abi armeabi-v7a --xnnpack --nnapi -N",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "nnapi"),
    ),
    BuildTarget(
        target="android-x86_64-static",
        args="--static --android --android_abi x86_64 --xnnpack --nnapi -N",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "nnapi"),
    ),
    BuildTarget(
        target="android-x86-static",
        args="--static --android --android_abi x86 --xnnpack --nnapi -N",
        runs_on="ubuntu-22.04",
        providers=("xnnpack", "nnapi"),
    ),
]

UNIVERSAL_TARGETS = [
    UniversalTarget(
        target="macos-universal-static",
        source_aarch64_target="macos-aarch64-static",
        source_x86_64_target="macos-x86_64-static",
    ),
    UniversalTarget(
        target="ios-simulator-universal-static",
        source_aarch64_target="ios-simulator-aarch64-static",
        source_x86_64_target="ios-simulator-x86_64-static",
    ),
]

BUILD_TARGETS_BY_NAME = {target.target: target for target in BUILD_TARGETS}
UNIVERSAL_TARGETS_BY_NAME = {target.target: target for target in UNIVERSAL_TARGETS}
ALL_TARGET_NAMES = [target.target for target in BUILD_TARGETS + UNIVERSAL_TARGETS]


def parse_enabled_input(raw: str | None, default: bool = True) -> bool:
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() == "true"


def provider_inputs_from_env() -> Dict[str, bool]:
    return {
        "xnnpack": parse_enabled_input(os.environ.get("ENABLE_XNNPACK")),
        "openvino": parse_enabled_input(os.environ.get("ENABLE_OPENVINO")),
        "directml": parse_enabled_input(os.environ.get("ENABLE_DIRECTML")),
        "coreml": parse_enabled_input(os.environ.get("ENABLE_COREML")),
        "nnapi": parse_enabled_input(os.environ.get("ENABLE_NNAPI")),
    }


def append_unique(values: List[str], new_values: Iterable[str]) -> None:
    seen = set(values)
    for value in new_values:
        if value not in seen:
            values.append(value)
            seen.add(value)


def parse_requested_targets(raw_targets: str) -> tuple[List[str], List[str]]:
    compact_targets = "".join(raw_targets.split())

    if not compact_targets:
        raise TargetResolutionError(
            "No build targets selected. Check target-all or select at least one target checkbox."
        )

    if compact_targets == "all":
        return (
            [target.target for target in BUILD_TARGETS],
            [target.target for target in UNIVERSAL_TARGETS],
        )

    build_targets: List[str] = []
    universal_targets: List[str] = []

    for name in compact_targets.split(","):
        if not name:
            continue
        if name in BUILD_TARGETS_BY_NAME:
            append_unique(build_targets, [name])
        elif name in UNIVERSAL_TARGETS_BY_NAME:
            append_unique(universal_targets, [name])
        else:
            raise TargetResolutionError(
                f"Unknown build target '{name}'. Select one of: {', '.join(ALL_TARGET_NAMES)}."
            )

    if not build_targets and not universal_targets:
        raise TargetResolutionError(
            "No build targets selected. Check target-all or select at least one target checkbox."
        )

    return build_targets, universal_targets


def resolve_targets(
    raw_targets: str,
    provider_inputs: Dict[str, bool] | None = None,
    include_universal_prerequisites: bool = True,
) -> Resolution:
    provider_inputs = provider_inputs or DEFAULT_PROVIDER_INPUTS
    selected_build_names, selected_universal_names = parse_requested_targets(raw_targets)

    if include_universal_prerequisites:
        for name in selected_universal_names:
            append_unique(selected_build_names, UNIVERSAL_TARGETS_BY_NAME[name].source_targets)
    else:
        for name in selected_universal_names:
            missing = [
                source
                for source in UNIVERSAL_TARGETS_BY_NAME[name].source_targets
                if source not in selected_build_names
            ]
            if missing:
                raise TargetResolutionError(
                    f"Universal target '{name}' requires source target(s): {', '.join(missing)}."
                )

    selected_templates = [
        BUILD_TARGETS_BY_NAME[name]
        for name in selected_build_names
    ]

    selected_provider_support = {
        provider
        for target in selected_templates
        for provider in target.providers
    }
    notices = []
    for provider, enabled in provider_inputs.items():
        if enabled and provider not in selected_provider_support:
            notices.append(
                f"enable-{provider} is true, but no selected target supports "
                f"{PROVIDER_LABELS[provider]}; no {PROVIDER_FLAGS[provider]} flag will be added."
            )

    build_matrix = [
        target.matrix_entry(provider_inputs)
        for target in selected_templates
    ]
    universal_matrix = [
        UNIVERSAL_TARGETS_BY_NAME[name].matrix_entry()
        for name in selected_universal_names
    ]

    return Resolution(
        build_targets=build_matrix,
        universal_targets=universal_matrix,
        notices=notices,
    )


def write_github_outputs(output_path: Path, values: Dict[str, str]) -> None:
    with output_path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--targets",
        default=os.environ.get("SELECTED_TARGETS", ""),
        help="Comma-separated exact target names, or all.",
    )
    parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT"),
        help="Path to a GitHub Actions output file.",
    )
    parser.add_argument(
        "--no-include-universal-prerequisites",
        action="store_true",
        help="Require universal source targets to already be selected.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        resolution = resolve_targets(
            raw_targets=args.targets,
            provider_inputs=provider_inputs_from_env(),
            include_universal_prerequisites=not args.no_include_universal_prerequisites,
        )
    except TargetResolutionError as exc:
        print(f"::error::{exc}")
        return 1

    for notice in resolution.notices:
        print(f"::notice::{notice}")

    print(
        f"Selected {len(resolution.build_targets)} build target(s): "
        f"{','.join(resolution.build_target_names)}"
    )
    for target in resolution.build_targets:
        print(f"{target['target']} build args: {target['args']}")

    if resolution.universal_targets:
        print(
            f"Selected {len(resolution.universal_targets)} universal target(s): "
            f"{','.join(resolution.universal_target_names)}"
        )
        for target in resolution.universal_targets:
            print(
                f"{target['target']} sources: "
                f"{target['source_aarch64_target']}, {target['source_x86_64_target']}"
            )

    outputs = resolution.output_values()
    if args.github_output:
        write_github_outputs(Path(args.github_output), outputs)
    if args.json:
        print(json.dumps(outputs, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    sys.exit(main())
