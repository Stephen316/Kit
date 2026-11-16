import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from decimal import Decimal
from types import MappingProxyType

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
from interchange.serialization.JsonCodec import LoadJson
from interchange.serialization.MigrationRegistry import KMigrationRegistry
from interchange.serialization.TypeRegistry import KTypeRegistry
from interchange.serialization.Wire import ResolveField

from SemanticGraph import build_graph, evidence_digest
from SemanticMatching import match_graphs

QUANTITIES = {"length_mm", "angle_rad", "dimensionless", "area_mm2", "volume_mm3"}
DOCUMENT_BYTES = 32 * 1024 * 1024
IMPLEMENTATION_SHA256 = {
    name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    for name in ("SemanticComparison.py", "SemanticGraph.py", "SemanticMatching.py")
}


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("comparison JSON contains duplicate keys")
    return result


def finite_constant(value):
    raise ValueError("comparison JSON contains a nonfinite constant")


def codec_float(token):
    value = float(token)
    if not math.isfinite(value) or Decimal(token) != Decimal(str(value)):
        raise ValueError("comparison JSON numeric literal loses precision in the codec")
    return value


def record_aliases(record):
    name = record.get("$type")
    target = KTypeRegistry.get(name) if isinstance(name, str) else None
    if target is None or not is_dataclass(target):
        return
    known = {field.name for field in fields(target)}
    arguments = {key: value for key, value in record.items() if key != "$type"}
    slots = [ResolveField(target, key) for key in arguments]
    slots = [slot for slot in slots if slot in known]
    if len(slots) != len(set(slots)):
        raise ValueError("comparison JSON contains colliding record field aliases")
    migration = KMigrationRegistry.get(target)
    if migration is None:
        return
    decoded = {key: FromData(value) for key, value in arguments.items()}
    migrated = migration(MappingProxyType(decoded))
    slots = [ResolveField(target, key) for key in migrated]
    slots = [slot for slot in slots if slot in known]
    if len(slots) != len(set(slots)):
        raise ValueError(
            "comparison record migration introduces colliding field aliases"
        )


def pinned_bytes(path, expected, limit):
    if re.fullmatch("[0-9a-f]{64}", expected) is None:
        raise ValueError("comparison input requires an exact lowercase SHA-256")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or (
        getattr(before, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise ValueError("comparison input must be a plain regular file")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    with os.fdopen(descriptor, "rb") as source:
        details = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_size > limit
            or (details.st_dev, details.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise ValueError("comparison input must be a bounded regular file")
        content = source.read(limit + 1)
    if len(content) > limit or hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("comparison input size or SHA-256 differs from its pin")
    return content


def bounded_json(content):
    value = json.loads(
        content,
        object_pairs_hook=unique_object,
        parse_constant=finite_constant,
        parse_float=codec_float,
    )
    pending = [(value, 0)]
    records = []
    visited = 0
    while pending:
        current, depth = pending.pop()
        visited += 1
        if visited > 500000 or depth > 64:
            raise ValueError("comparison JSON exceeds its structural limit")
        if isinstance(current, dict):
            if "$type" in current:
                records.append(current)
            pending.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
        elif isinstance(current, float) and not math.isfinite(current):
            raise ValueError("comparison JSON contains a nonfinite magnitude")
        elif isinstance(current, str) and len(current) > DOCUMENT_BYTES:
            raise ValueError("comparison JSON text exceeds its length limit")
    for record in reversed(records):
        record_aliases(record)
    return value


def document_input(path, checksum):
    content = pinned_bytes(path, checksum, DOCUMENT_BYTES)
    bounded_json(content)
    document = LoadJson(content.decode("utf-8"))
    if not isinstance(document, CadDocument):
        raise ValueError("comparison input does not describe a CadDocument")
    document.assert_valid()
    return document


def tolerance_input(path, checksum):
    value = bounded_json(pinned_bytes(path, checksum, 65536))
    if not isinstance(value, dict) or set(value) != QUANTITIES:
        raise ValueError("declare exactly five quantity-specific absolute tolerances")
    if any(
        type(item) not in (int, float) or not math.isfinite(item) or item < 0
        for item in value.values()
    ):
        raise ValueError("absolute tolerances must be finite nonnegative numbers")
    return value


def compare_documents(
    first, second, tolerances, first_unit, second_unit, max_candidates
):
    if any(
        hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != pin
        for name, pin in IMPLEMENTATION_SHA256.items()
    ):
        raise ValueError("comparison implementation changed after it was imported")
    left = build_graph(first, first_unit)
    right = build_graph(second, second_unit)
    result = match_graphs(left, right, tolerances, max_candidates)
    differences = sum(bool(item["differences"]) for item in result["matches"])
    if result["search_limited"]:
        status = "incomplete"
    elif result["ambiguous"]:
        status = "ambiguous"
    elif (
        differences
        or result["reference_differences"]
        or result["unmatched_left"]
        or result["unmatched_right"]
    ):
        status = "different"
    elif left["issues"] or right["issues"]:
        status = "unresolved"
    else:
        status = "equal_observed_graph"
    for match in result["matches"]:
        match["source_records"] = {
            "left": {
                key: left["nodes"][match["left"]].get(key) for key in ("path", "label")
            },
            "right": {
                key: right["nodes"][match["right"]].get(key)
                for key in ("path", "label")
            },
        }
    if any(
        hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() != pin
        for name, pin in IMPLEMENTATION_SHA256.items()
    ):
        raise ValueError("comparison implementation changed during evaluation")
    return {
        "comparison_version": 1,
        "implementation_sha256": dict(IMPLEMENTATION_SHA256),
        "scope": "portable_semantic_graph_observation",
        "status": status,
        "semantic_qualification": "unverified",
        "independent_source_inventory": "not_supplied",
        "native_acceptance": "not_established",
        "absolute_tolerances": tolerances,
        "comparison": result,
        "sources": {
            side: {
                "format": document.source.format_id,
                "source_sha256": document.source.sha256,
                "source_identity_sha256": evidence_digest(document.source),
                "application_version": document.source.application_version,
                "container_version": document.source.container_version,
                "declared_geometry_unit": unit,
                "nodes": len(graph["nodes"]),
                "fields": graph["field_count"],
                "unresolved": graph["issues"],
                "observations": graph["observations"],
            }
            for side, document, unit, graph in (
                ("left", first, first_unit, left),
                ("right", second, second_unit, right),
            )
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare pinned CadDocument graphs without inferring native qualification"
    )
    for side in ("first", "second"):
        parser.add_argument(f"--{side}", type=Path, required=True)
        parser.add_argument(f"--{side}-sha256", required=True)
        parser.add_argument(
            f"--{side}-geometry-unit",
            choices=("mm", "cm", "m", "in", "ft"),
            required=True,
        )
    parser.add_argument("--tolerances", type=Path, required=True)
    parser.add_argument("--tolerances-sha256", required=True)
    parser.add_argument("--max-candidates", default="20000")
    args = parser.parse_args()
    try:
        args.max_candidates = int(args.max_candidates)
        if not 1 <= args.max_candidates <= 100000:
            raise ValueError("candidate budget must be between 1 and 100000")
        first = document_input(args.first, args.first_sha256)
        second = document_input(args.second, args.second_sha256)
        tolerances = tolerance_input(args.tolerances, args.tolerances_sha256)
        result = compare_documents(
            first,
            second,
            tolerances,
            args.first_geometry_unit,
            args.second_geometry_unit,
            args.max_candidates,
        )
        result["input_sha256"] = {
            "left": args.first_sha256,
            "right": args.second_sha256,
            "tolerances": args.tolerances_sha256,
        }
        content = json.dumps(
            result, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if len(content.encode()) > DOCUMENT_BYTES:
            raise ValueError("comparison report exceeds 32 MiB")
        print(content)
        if result["status"] == "equal_observed_graph":
            return 0
        return 2 if result["status"] == "different" else 3
    except (
        LookupError,
        OSError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ) as error:
        print(f"semantic comparison refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
