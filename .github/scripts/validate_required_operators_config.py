#!/usr/bin/env python3
"""Decode and validate ONNX Runtime reduced-operator config files."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple


DOMAIN_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
OPERATOR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ConfigError(ValueError):
    """Validation error that is safe to print without echoing config contents."""


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def decode_base64_payload(payload: str) -> bytes:
    compact_payload = "".join(payload.split())
    if not compact_payload:
        raise ConfigError("required operators config base64 payload is empty")

    try:
        return base64.b64decode(compact_payload, validate=True)
    except binascii.Error as exc:
        raise ConfigError("required operators config input is not valid base64") from exc


def parse_positive_int_list(value: str, line_number: int) -> None:
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(not part for part in parts):
        raise ConfigError(f"line {line_number}: opset list contains an empty value")

    for part in parts:
        try:
            opset = int(part)
        except ValueError as exc:
            raise ConfigError(f"line {line_number}: opset values must be integers") from exc
        if opset <= 0:
            raise ConfigError(f"line {line_number}: opset values must be positive")


def validate_type_json(value: Any, line_number: int) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"line {line_number}: type-reduction suffix must be a JSON object")

    for key in ("inputs", "outputs"):
        if key in value and not isinstance(value[key], dict):
            raise ConfigError(f"line {line_number}: type-reduction '{key}' value must be a JSON object")

    if "custom" in value and not isinstance(value["custom"], list):
        raise ConfigError(f"line {line_number}: type-reduction 'custom' value must be a JSON array")


def parse_operator_list(value: str, line_number: int) -> Tuple[int, bool]:
    if not value:
        raise ConfigError(f"line {line_number}: operator list is empty")

    decoder = json.JSONDecoder()
    operator_count = 0
    has_type_reduction = False
    cursor = 0

    while cursor < len(value):
        while cursor < len(value) and value[cursor].isspace():
            cursor += 1

        if cursor >= len(value):
            raise ConfigError(f"line {line_number}: operator list has a trailing comma")

        name_start = cursor
        while cursor < len(value) and value[cursor] not in ",{":
            cursor += 1

        operator = value[name_start:cursor].strip()
        if not operator:
            raise ConfigError(f"line {line_number}: operator name is empty")
        if not OPERATOR_RE.match(operator):
            raise ConfigError(f"line {line_number}: operator name has an unsupported shape")

        if cursor < len(value) and value[cursor] == "{":
            try:
                type_info, consumed = decoder.raw_decode(value[cursor:])
            except json.JSONDecodeError as exc:
                raise ConfigError(f"line {line_number}: type-reduction JSON suffix is malformed") from exc

            validate_type_json(type_info, line_number)
            has_type_reduction = True
            cursor += consumed

            while cursor < len(value) and value[cursor].isspace():
                cursor += 1

        operator_count += 1

        if cursor == len(value):
            break

        if value[cursor] != ",":
            raise ConfigError(f"line {line_number}: expected comma between operators")

        cursor += 1

    return operator_count, has_type_reduction


def validate_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.is_file():
        raise ConfigError("required operators config file does not exist")

    config_bytes = config_path.read_bytes()
    if not config_bytes:
        raise ConfigError("required operators config file is empty")

    try:
        config_text = config_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError("required operators config file must be UTF-8 text") from exc

    operator_count = 0
    operator_line_count = 0
    has_type_reduction = False
    has_global_type_filter = False
    no_ops_means_all_ops = False

    for line_number, raw_line in enumerate(config_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("!"):
            if line.startswith("!globally_allowed_types;"):
                if has_global_type_filter:
                    raise ConfigError(f"line {line_number}: globally allowed types may only be specified once")
                types = [entry.strip() for entry in line.split(";", 1)[1].split(",")]
                if not types or any(not entry for entry in types):
                    raise ConfigError(f"line {line_number}: globally allowed types list is empty")
                has_global_type_filter = True
                continue

            if line == "!no_ops_specified_means_all_ops_are_required":
                no_ops_means_all_ops = True
                continue

            raise ConfigError(f"line {line_number}: unsupported reduced-operator directive")

        parts = [part.strip() for part in line.split(";")]
        if len(parts) != 3:
            raise ConfigError(f"line {line_number}: expected 'domain;opset;operators' shape")

        domain, opsets, operators = parts
        if not domain:
            raise ConfigError(f"line {line_number}: operator domain is empty")
        if not DOMAIN_RE.match(domain):
            raise ConfigError(f"line {line_number}: operator domain has an unsupported shape")

        parse_positive_int_list(opsets, line_number)
        line_operator_count, line_has_type_reduction = parse_operator_list(operators, line_number)
        operator_count += line_operator_count
        operator_line_count += 1
        has_type_reduction = has_type_reduction or line_has_type_reduction

    return {
        "byte_count": len(config_bytes),
        "sha256": hashlib.sha256(config_bytes).hexdigest(),
        "operator_count": operator_count,
        "operator_line_count": operator_line_count,
        "has_type_reduction": has_type_reduction,
        "has_global_type_filter": has_global_type_filter,
        "no_ops_specified_means_all_ops_are_required": no_ops_means_all_ops,
    }


def append_github_outputs(output_path: Path, values: Dict[str, str]) -> None:
    with output_path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def write_metadata(metadata_path: Path, metadata: Dict[str, Any]) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", help="Path to an existing required operators config file")
    parser.add_argument("--base64-env", help="Environment variable containing a base64-encoded config")
    parser.add_argument("--output", help="Path to write the decoded config when --base64-env is used")
    parser.add_argument("--github-output", help="Path to a GitHub Actions output file")
    parser.add_argument("--metadata-output", help="Path to write safe reduced-ops metadata JSON")
    parser.add_argument(
        "--enable-reduced-operator-type-support",
        action="store_true",
        help="Record that reduced operator type support was requested",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        if args.base64_env:
            if not args.output:
                raise ConfigError("--output is required when --base64-env is used")
            payload = os.environ.get(args.base64_env, "")
            decoded = decode_base64_payload(payload)
            config_path = Path(args.output)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_bytes(decoded)
        elif args.config:
            config_path = Path(args.config)
        else:
            raise ConfigError("a config path or --base64-env is required")

        metadata = validate_config(config_path)
        if (
            args.enable_reduced_operator_type_support
            and metadata["has_type_reduction"]
            and metadata["has_global_type_filter"]
        ):
            raise ConfigError(
                "per-operator type reduction entries and globally allowed types are mutually exclusive"
            )
    except OSError as exc:
        fail(str(exc))
    except ConfigError as exc:
        fail(str(exc))

    sha256 = metadata["sha256"]
    safe_metadata = {
        "reduced_ops": True,
        "required_operators_config_sha256": sha256,
        "required_operators_config_sha256_short": sha256[:12],
        "required_operators_config_bytes": metadata["byte_count"],
        "required_operator_count": metadata["operator_count"],
        "required_operator_line_count": metadata["operator_line_count"],
        "required_operator_config_has_type_reduction": metadata["has_type_reduction"],
        "required_operator_config_has_global_type_filter": metadata["has_global_type_filter"],
        "no_ops_specified_means_all_ops_are_required": metadata["no_ops_specified_means_all_ops_are_required"],
        "enable_reduced_operator_type_support": args.enable_reduced_operator_type_support,
    }

    if args.metadata_output:
        write_metadata(Path(args.metadata_output), safe_metadata)

    if args.github_output:
        append_github_outputs(
            Path(args.github_output),
            {
                "path": str(config_path),
                "sha256": sha256,
                "sha256_short": sha256[:12],
                "byte_count": str(metadata["byte_count"]),
                "operator_count": str(metadata["operator_count"]),
                "has_type_reduction": str(metadata["has_type_reduction"]).lower(),
            },
        )

    print(
        "Validated required operators config: "
        f"bytes={metadata['byte_count']} "
        f"operators={metadata['operator_count']} "
        f"sha256={sha256}"
    )


if __name__ == "__main__":
    main()
