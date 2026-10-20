"""Experimental Fusion parameter reader, not a general feature-tree decoder.

Reads observed numeric-parameter record layouts rather than known values or
fixed file offsets. Geometry and feature interpretation live in other modules.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from fusion_archive import read_members
from fusion_records import record_fragments
from fusion_metadata import design_records


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


def decode_stream(data, records=None):
    """Decode observed numeric model-parameter records, regardless of role name."""
    parameters, rejected = [], []
    for record in record_fragments(data) if records is None else records:
        body = data[record.body:record.end]
        if len(body) < 31 or body[:7] != b"\0" * 7 or body[7:11] != b"\x06\0\0\0":
            continue
        try:
            if body[20] != 1 or body[29:31] != b"\0\0":
                raise ValueError("Unsupported binding-reference prefix")
            binding_id = struct.unpack_from("<Q", body, 21)[0]
            expression, cursor = read_string(body, 31)
            metadata = body[cursor:cursor + 10]
            cursor += 10
            role_offset = cursor
            role, cursor = read_string(body, cursor)
            reserved_text, cursor = read_string(body, cursor)
            units, cursor = read_string(body, cursor)
            name, cursor = read_string(body, cursor)
            if not role or reserved_text or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
                raise ValueError("Unrecognized parameter text fields")
            if cursor + 20 != len(body):
                raise ValueError("Unrecognized numeric parameter suffix length")
            value = struct.unpack_from("<d", body, cursor)[0]
            if not math.isfinite(value):
                raise ValueError("Non-finite parameter")
            item = {
                "role": role, "parameter_name": name, "display_units": units,
                "raw_float64": value, "role_offset": record.body + role_offset,
                "value_offset": record.body + cursor,
                "expression_candidates": [expression] if expression else [],
                "parameter_object_id": record.object_id,
                "class_guid": record.class_guid,
                "declared_binding_object_id": binding_id,
                "expression_metadata_hex": metadata.hex(),
                "layout": "observed numeric-parameter record, UTF16LE text and LE float64",
            }
            if units in ("deg", "rad"):
                item.update(internal_units="rad", hypothesized_value_degrees=math.degrees(value))
            elif units in ("mm", "cm", "m", "in", "ft"):
                item.update(internal_units="cm", hypothesized_value_mm=value * 10)
            elif not units or units == "unitless":
                item["internal_units"] = "unitless"
            else:
                item["internal_units"] = "Unclassified"
            parameters.append(item)
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            rejected.append({"object_id": record.object_id, "offset": record.start, "reason": str(error)})
    return sorted(parameters, key=lambda p: p["role_offset"]), rejected


def decode_file(path, zstd_library=None):
    members = read_members(path, zstd_library)
    records = []
    for name, data in members.items():
        if name.endswith("FusionDesignSegmentType1/BulkStream.dat"):
            fragments, index = design_records(data, members.get(name.replace("BulkStream.dat", "MetaStream.dat")))
            parameters, rejected = decode_stream(data, fragments)
            records.append({"member": name, "parameters": parameters, "rejected": rejected,
                            "record_index": index})
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
