"""Experimental Fusion parameter reader, not a general feature-tree decoder.

Finds observed role-labelled records rather than known numeric values or fixed
file offsets. Object references, extrusion ownership and geometry are not decoded.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from fusion_archive import read_members


ROLES = {"AlongDistance": {"mm", "cm", "m", "in", "ft"}, "TaperAngle": {"deg", "rad"}}


def read_string(data, position):
    if position < 0 or position + 4 > len(data):
        raise ValueError("Truncated string length")
    length = struct.unpack_from("<I", data, position)[0]
    end = position + 4 + 2 * length
    if length > 1024 or end > len(data):
        raise ValueError("Invalid string extent")
    text = data[position + 4:end].decode("utf-16le")
    if not all(c.isprintable() for c in text):
        raise ValueError("Non-printable string")
    return text, end


def decode_stream(data):
    parameters, rejected = [], []
    roles = dict(ROLES)
    for dimension in ("Radial", "Diameter", "Linear", "Angular"):
        pattern = re.escape((dimension + " Dimension-").encode("utf-16le")) + rb"(?:[0-9]\x00)+"
        for match in re.finditer(pattern, data):
            try:
                role, _ = read_string(data, match.start() - 4)
            except (ValueError, UnicodeError, struct.error):
                continue
            if re.fullmatch(dimension + r" Dimension-[0-9]+", role):
                roles[role] = ROLES["TaperAngle" if dimension == "Angular" else "AlongDistance"]
    for role, units in roles.items():
        marker = struct.pack("<I", len(role)) + role.encode("utf-16le")
        for match in re.finditer(re.escape(marker), data):
            start = match.start()
            try:
                actual_role, cursor = read_string(data, start)
                unknown_text, cursor = read_string(data, cursor)
                display_units, cursor = read_string(data, cursor)
                name, cursor = read_string(data, cursor)
                if actual_role != role or unknown_text or display_units not in units:
                    raise ValueError("Unsupported parameter layout or units")
                if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                    raise ValueError("Unexpected parameter name")
                value = struct.unpack_from("<d", data, cursor)[0]
                if not math.isfinite(value):
                    raise ValueError("Non-finite parameter")
                # Observed separator has ten bytes; its complete semantics are unknown.
                expressions = []
                for position in range(max(0, start - 1024), start - 13):
                    try:
                        expression, end = read_string(data, position)
                    except (ValueError, UnicodeError, struct.error):
                        continue
                    if expression and end == start - 10:
                        expressions.append(expression)
                item = {
                    "role": role, "parameter_name": name,
                    "display_units": display_units, "raw_float64": value,
                    "role_offset": start, "value_offset": cursor,
                    "expression_candidates": expressions,
                    "layout": "u32-length UTF16LE strings followed by LE float64",
                }
                # Internal units are research hypotheses checked against API truth.
                if role == "TaperAngle" or role.startswith("Angular Dimension-"):
                    item["hypothesized_value_degrees"] = math.degrees(value)
                else:
                    item["hypothesized_value_mm"] = value * 10
                parameters.append(item)
            except (ValueError, UnicodeError, struct.error) as error:
                rejected.append({"role": role, "offset": start, "reason": str(error)})
    return sorted(parameters, key=lambda p: p["role_offset"]), rejected


def decode_file(path, zstd_library=None):
    members = read_members(path, zstd_library)
    records = []
    for name, data in members.items():
        if name.endswith("FusionDesignSegmentType1/BulkStream.dat"):
            parameters, rejected = decode_stream(data)
            records.append({"member": name, "parameters": parameters, "rejected": rejected})
    return {
        "file": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "scope": "Role-labelled parameter records only; no verified feature ownership or topology",
        "streams": records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_file(p, args.zstd_library) for p in args.files], indent=2))
