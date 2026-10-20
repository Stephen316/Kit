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


def _bound_text_binding(data, records, binding_id, parameter_id, text, stored_index):
    """Validate the captured SketchText model binding and its reciprocal copies."""
    def typed(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity]
        if len(matches) != 1 or matches[0].class_guid != guid:
            raise ValueError("Bound Text typed reference missing, ambiguous or wrong class")
        record = matches[0]
        return record, data[record.body:record.end]

    def reference(payload, offset):
        if payload[offset:offset+1] != b"\1" or payload[offset+9:offset+11] != b"\0\0":
            raise ValueError("Invalid bound Text reference framing")
        return struct.unpack_from("<Q", payload, offset+1)[0]

    record, body = typed(binding_id, "e5460b7b-000b-4a70-ab52-4c2fcc470eb2")
    if len(body) >= 21 and struct.unpack_from("<I", body, 16)[0] == 3:
        from decode_parameter_text_bindings import validate_numbered_text_binding
        return validate_numbered_text_binding(data, records, binding_id, parameter_id, text, stored_index)
    if body[:5] != bytes.fromhex("0101000000") or body[16:21] != bytes.fromhex("0100000000"):
        raise ValueError("Unobserved bound Text binding prefix/value kind")
    owner = reference(body, 5)
    typed(owner, "8DA771B7-52ED-42FC-94E2-2353FE141373")
    cached, cursor = read_string(body, 21, allow_text_controls=True)
    if (cached != text or len(body) != cursor+56 or reference(body, cursor) != parameter_id
            or struct.unpack_from("<II", body, cursor+11) != (stored_index, 0)
            or reference(body, cursor+19) != owner or body[cursor+30:cursor+33] != bytes.fromhex("010000")
            or body[cursor+44] != 0 or reference(body, cursor+45) != owner):
        raise ValueError("Bound Text value/parameter/index/owner copies disagree")
    bookkeeping = reference(body, cursor+33)
    _, bookkeeping_body = typed(bookkeeping, "6CCF41D5-40BE-48ED-A834-18F3EAED6C57")
    if len(bookkeeping_body) != 39 or reference(bookkeeping_body, 12) != binding_id:
        raise ValueError("Bound Text bookkeeping link does not reciprocate binding")
    return {"binding_owner_object_id": owner, "binding_offset": record.start,
            "binding_bookkeeping_object_id": bookkeeping,
            "binding_value_representation": "UTF16LE",
            "binding_status": "Typed SketchText model binding with matching cached text and reciprocal parameter/index/owner copies"}


def decode_stream(data, records=None):
    """Decode observed numeric/Text model and user parameter layouts."""
    parameters, rejected = [], []
    records = list(record_fragments(data) if records is None else records)
    for record in records:
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
            if value_kind == 1 and units != "Text":
                raise ValueError("Unobserved Text parameter units")
            if value_kind == 1 and binding_id is not None and (
                    record.class_guid != "7A6A3D31-BE74-4E19-9115-20642944C2E4"
                    or not re.fullmatch(r"Text[1-9][0-9]*-Text", role)):
                raise ValueError("Only observed SketchText bound Text model parameters are decoded")
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
                item.update(text_value=reserved_text, value_type="Text", internal_units="Text",
                            layout="observed Text user parameter with stored expression and text value")
                if binding_id is not None:
                    item.update(_bound_text_binding(data, records, binding_id, record.object_id, reserved_text, stored_index))
                    item.update(parameter_kind="ModelParameter", stored_parameter_index=stored_index,
                                layout="observed SketchText model parameter with reciprocal UTF16LE text binding")
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
            from decode_expression_dependencies import derive_expression_dependencies
            expression_dependencies = derive_expression_dependencies(parameters, tables)
            records.append({"member": name, "parameters": parameters, "rejected": rejected,
                            "record_index": index, "parameter_tables": tables,
                            "derived_expression_dependencies": expression_dependencies})
    return {
        "file": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "scope": "Observed numeric/Text model and user parameters with reciprocal name tables; no expression evaluation or feature regeneration",
        "streams": records,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_file(p, args.zstd_library) for p in args.files], indent=2))
