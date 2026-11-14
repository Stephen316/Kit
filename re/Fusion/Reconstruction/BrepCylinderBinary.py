import argparse
import hashlib
import json
import struct
from pathlib import Path

from BrepCylinder import CountedText, Cylinder, Keyword, Reference, build_records
from BrepTokens import encode_token


def name_tokens(name):
    parts = name.split("-")
    return [(14 if index < len(parts) - 1 else 13, part) for index, part in enumerate(parts)]


def field_token(item):
    value = item.value
    if isinstance(value, Reference):
        return 12, value.index
    if isinstance(value, CountedText):
        return 7, value.value
    if isinstance(value, Keyword):
        if value.value in ("forward", "single", "forward_v", "I"):
            return 11, None
        if value.value in ("reversed", "double", "reverse_v"):
            return 10, None
        raise ValueError("Unknown keyword semantics")
    if isinstance(value, tuple):
        if item.name.endswith("_mm"):
            value = tuple(component / 10 for component in value)
        tag = 19 if item.name in ("origin_mm", "center_mm", "position_mm") else 20
        return tag, value
    if isinstance(value, int):
        return 4, value
    if isinstance(value, float):
        return 6, value / 10 if item.name.endswith("_mm") else value
    raise ValueError("Unknown semantic field")


def encode(model):
    records = build_records(model)
    tokens = [(7, "Kit"), (7, "Independent ASM research"), (7, "Thu Nov 12 00:00:00 2026"), (6, 10.0), (6, 1e-6), (6, 1e-10)]
    rows = []
    for index, record in enumerate(records):
        fields = [field_token(item) for item in record.fields]
        tokens.extend(name_tokens(record.name))
        tokens.extend(fields)
        tokens.append((17, None))
        rows.append({"index": index, "name": record.name, "fields": [{"name": item.name, "tag": wire[0], "value": wire[1], "derivation": item.derivation} for item, wire in zip(record.fields, fields)]})
    tokens.extend(name_tokens("End-of-ASM-data"))
    result = b"ASM BinaryFile8" + struct.pack("<4q", 23200, 0, 2, 2)
    result += b"".join(encode_token(tag, value) for tag, value in tokens)
    return result, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--radius-mm", type=float, default=15.0)
    parser.add_argument("--height-mm", type=float, default=11.0)
    parser.add_argument("--base-mm", type=float, nargs=3, default=(20.0, -30.0, 5.0))
    args = parser.parse_args()
    model = Cylinder(args.radius_mm, args.height_mm, tuple(args.base_mm))
    data, records = encode(model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    evidence = {
        "artifact_kind": "Independently authored no-history ASM binary research solid; native acceptance pending",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "input_model": {"radius_mm": model.radius_mm, "height_mm": model.height_mm, "base_mm": model.base_mm},
        "length_encoding": "Every length field explicitly converts semantic millimetres to binary centimetres",
        "header": {"save_format": 23200, "stored_records": 0, "top_level_entity_count": 2, "flags": 2, "scale_metadata": 10},
        "source_dependencies": [],
        "records": records,
        "limitations": ["No history partition", "No Fusion Design body-map or persistent identity attributes", "Native import must be established separately"],
    }
    args.output.with_suffix(".binary-derivation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({key: evidence[key] for key in ("sha256", "bytes", "header")}, indent=2))


if __name__ == "__main__":
    main()
