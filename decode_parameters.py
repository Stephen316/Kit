"""Experimental Fusion parameter reader, not a general feature-tree decoder.

Reads observed numeric/text parameter record layouts rather than known values or
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


def read_string(data, position, *, allow_text_controls=False):
    if position < 0 or position + 4 > len(data):
        raise ValueError("Truncated string length")
    length = struct.unpack_from("<I", data, position)[0]
    end = position + 4 + 2 * length
    if length > 1024 or end > len(data):
        raise ValueError("Invalid string extent")
    text = data[position + 4:end].decode("utf-16le")
    if not all(c.isprintable() or (allow_text_controls and c in "\r\n\t") for c in text):
        raise ValueError("Non-printable string")
    return text, end


def decode_stream(data, records=None):
    """Decode observed numeric model parameters and numeric/text user records."""
    parameters, rejected = [], []
    for record in record_fragments(data) if records is None else records:
        body = data[record.body:record.end]
        if len(body) < 31 or body[:7] != b"\0" * 7 or body[7:11] != b"\x06\0\0\0":
            continue
        try:
            if body[11] != 0:
                raise ValueError("Unsupported parameter comment prefix")
            comment, cursor = read_string(body, 12, allow_text_controls=True)
            stored_index = struct.unpack_from("<I", body, cursor)[0]
            cursor += 4
            if body[cursor] == 1 and body[cursor+9:cursor+11] == b"\0\0":
                binding_id = struct.unpack_from("<Q", body, cursor+1)[0]
                text_start = cursor+11
            elif body[cursor] == 0:
                binding_id, text_start = None, cursor+1
            else:
                raise ValueError("Unsupported binding-reference prefix")
            expression, cursor = read_string(body, text_start, allow_text_controls=True)
            metadata = body[cursor:cursor + 10]
            if len(metadata) != 10:
                raise ValueError("Truncated parameter expression metadata")
            value_kind = struct.unpack_from("<I", metadata)[0]
            if value_kind not in (0, 1):
                raise ValueError("Unobserved parameter value type")
            if value_kind == 0 and any(c in expression for c in "\r\n\t"):
                raise ValueError("Unverified controls in numeric parameter expression")
            cursor += 10
            role_offset = cursor
            role, cursor = read_string(body, cursor)
            reserved_text, cursor = read_string(body, cursor, allow_text_controls=True)
            units, cursor = read_string(body, cursor)
            name, cursor = read_string(body, cursor)
            if (not role or (value_kind == 0 and reserved_text)
                    or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name)):
                raise ValueError("Unrecognized parameter text fields")
            if binding_id is None and (record.class_guid != "7A6A3D31-BE74-4E19-9115-20642944C2E4"
                                       or role != "User Parameter"):
                raise ValueError("Unobserved unbound parameter variant")
            if value_kind == 1 and (binding_id is not None or units != "Text"):
                raise ValueError("Only observed unbound Text user parameters are decoded")
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
                "comment": comment,
                "is_favorite": bool(metadata[7]) if metadata[7] in (0, 1) else None,
                "favorite_status": "Observed native favorite flag" if metadata[7] in (0, 1) else "Unverified native favorite flag",
                "layout": "observed numeric-parameter record, UTF16LE text and LE float64",
            }
            if binding_id is None:
                if metadata[7] not in (0, 1):
                    raise ValueError("Unobserved user-parameter favorite flag")
                item.update(parameter_kind="UserParameter",
                            comment=comment, is_favorite=bool(metadata[7]),
                            value_type="Text" if value_kind else "Numeric",
                            stored_parameter_index=stored_index,
                            layout="observed user parameter with absent feature-binding reference")
            if value_kind == 1:
                if body[cursor:cursor+8] != bytes(8):
                    raise ValueError("Unobserved text parameter numeric placeholder")
                item.pop("raw_float64")
                item.update(text_value=reserved_text, internal_units="Text",
                            layout="observed Text user parameter with stored expression and text value")
            elif units in ("deg", "rad"):
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
            from decode_parameter_tables import decode_parameter_tables
            tables = decode_parameter_tables(data, fragments, parameters)
            records.append({"member": name, "parameters": parameters, "rejected": rejected,
                            "record_index": index, "parameter_tables": tables})
    return {
        "file": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "scope": "Observed numeric model and numeric/text user parameters with reciprocal name tables; no expression evaluation or feature regeneration",
        "streams": records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_file(p, args.zstd_library) for p in args.files], indent=2))
