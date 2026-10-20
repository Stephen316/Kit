"""Experimental named-feature and parameter-reference decoding for Fusion.

Layouts are inferred from Fusion 2705.1.30 samples, not a complete schema.
Unknown fields remain unknown; no geometry, topology or file writing is provided.
"""

import argparse
from bisect import bisect_right
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from decode_parameters import decode_stream, read_string
from fusion_archive import read_members


@dataclass
class Record:
    start: int
    body: int
    end: int
    type_code: str
    object_id: int


def record_fragments(data):
    """Find observed headers; next-header bounds are provisional, not a grammar."""
    records = []
    for position in range(max(0, len(data) - 19)):
        length = struct.unpack_from("<I", data, position)[0]
        if not 1 <= length <= 4:
            continue
        code = data[position + 4:position + 4 + length]
        body = position + 16 + length
        if body > len(data) or not code.isdigit():
            continue
        identity = struct.unpack_from("<Q", data, position + 4 + length)[0]
        if identity >= 2**32 or data[body - 4:body] != b"\0" * 4:
            continue
        records.append(Record(position, body, len(data), code.decode(), identity))
    for current, following in zip(records, records[1:]):
        current.end = following.start
    return records


def named_features(data, records):
    features = []
    starts = [r.start for r in records]
    for kind in ("Sketch", "Extrude"):
        marker = struct.pack("<I", len(kind)) + kind.encode("utf-16le")
        for match in re.finditer(re.escape(marker), data):
            index = bisect_right(starts, match.start()) - 1
            if index < 0:
                continue
            record = records[index]
            chunk = data[record.body:record.end]
            try:
                _, cursor = read_string(chunk, match.start() - record.body)
                stored_index = struct.unpack_from("<Q", chunk, cursor)[0]
                if stored_index >= 2**32:
                    continue
                item = {
                    "kind": kind, "object_id": record.object_id,
                    "stored_index": stored_index, "record_offset": record.start,
                    "type_code": record.type_code, "parameters": [],
                }
                if kind == "Extrude":
                    name, _ = read_string(chunk, cursor + 8)
                    item["name"] = name or None
                else:
                    # The sketch feature points to a separate named sketch object.
                    if len(chunk) < 21 or chunk[12] != 1:
                        continue
                    root_id = struct.unpack_from("<Q", chunk, 13)[0]
                    roots = []
                    for candidate in records:
                        if candidate.object_id != root_id:
                            continue
                        body = data[candidate.body:candidate.end]
                        if len(body) <= 28 or body[0] != 1:
                            continue
                        try:
                            name, _ = read_string(body, 28)
                            roots.append(name)
                        except (ValueError, UnicodeError, struct.error):
                            continue
                    if len(roots) != 1:
                        continue
                    item.update({"name": roots[0] or None, "sketch_object_id": root_id})
                features.append(item)
            except (ValueError, UnicodeError, struct.error):
                continue
    return sorted(features, key=lambda f: f["record_offset"])


def attach_parameters(data, records, features, parameters):
    by_id = {f["object_id"]: f for f in features}
    starts = [r.start for r in records]
    pending = {}
    for parameter in parameters:
        index = bisect_right(starts, parameter["role_offset"]) - 1
        if index >= 0:
            pending.setdefault(records[index].object_id, []).append(parameter)
    attached = set()
    for record in records:
        body = data[record.body:record.end]
        if len(body) != 85 or body[:6] != b"\x01\x01\0\0\0\x01":
            continue
        owner = struct.unpack_from("<Q", body, 6)[0]
        if body[29] != 1 or body[-11] != 1 or body[-2:] != b"\0\0":
            continue
        if struct.unpack_from("<Q", body, len(body) - 10)[0] != owner:
            continue
        parameter_id = struct.unpack_from("<Q", body, 30)[0]
        choices = pending.get(parameter_id, [])
        if owner not in by_id or len(choices) != 1:
            continue
        parameter = choices[0]
        raw_value = data[parameter["value_offset"]:parameter["value_offset"] + 8]
        if body[21:29] != raw_value or parameter["role_offset"] in attached:
            continue
        by_id[owner]["parameters"].append({
            **parameter, "parameter_object_id": parameter_id,
            "binding_object_id": record.object_id, "binding_offset": record.start,
            "association": "explicit owner and parameter references with matching numeric payload",
        })
        attached.add(parameter["role_offset"])
    return [p for p in parameters if p["role_offset"] not in attached]


def sketch_references(data, records, features):
    by_feature = {f["object_id"]: f for f in features if f["kind"] == "Extrude"}
    by_sketch = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    for record in records:
        body = data[record.body:record.end]
        if len(body) < 50 or body[-11] != 1 or body[-2:] != b"\0\0":
            continue
        owner = struct.unpack_from("<Q", body, len(body) - 10)[0]
        if owner not in by_feature:
            continue
        matches = []
        for offset in range(len(body) - 4):
            if body[offset:offset + 4] != b"\x24\0\0\0":
                continue
            try:
                namespace, cursor = read_string(body, offset)
                identity, _ = read_string(body, cursor)
            except (ValueError, UnicodeError, struct.error):
                continue
            if (not re.fullmatch(r"[0-9a-fA-F-]{36}", namespace)
                    or not identity.isascii() or not identity.isdecimal()):
                continue
            sketch = by_sketch.get(int(identity))
            if sketch:
                matches.append({
                    "sketch_object_id": int(identity), "feature_object_id": sketch["object_id"],
                    "name": sketch["name"], "reference_record_offset": record.start,
                    "namespace_text": namespace,
                    "scope": "observed sketch reference; selected contour is not decoded",
                })
        if len(matches) == 1:
            by_feature[owner].setdefault("sketch_reference_candidates", []).extend(matches)


def decode_basics(path, zstd_library=None):
    streams = []
    for name, data in read_members(path, zstd_library).items():
        if not name.endswith("FusionDesignSegmentType1/BulkStream.dat"):
            continue
        records = record_fragments(data)
        features = named_features(data, records)
        parameters, rejected = decode_stream(data)
        unbound = attach_parameters(data, records, features, parameters)
        sketch_references(data, records, features)
        streams.append({
            "member": name, "features": features, "unbound_parameters": unbound,
            "rejected_parameters": rejected, "candidate_record_headers": len(records),
        })
    return {
        "file": str(path), "status": "experimental partial decoder",
        "scope": "Observed layouts in Fusion 2705.1.30; unsupported records remain undecoded",
        "limitations": [
            "Candidate header boundaries and field semantics are inferred from a small corpus.",
            "Type codes are local to the document and not treated as universal feature identifiers.",
            "No sketch geometry, constraints, exact profile selection, topology, or native writer.",
            "No general feature history, suppression, end-condition or operation-type decoder.",
        ],
        "streams": streams,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_basics(p, args.zstd_library) for p in args.files], indent=2))
