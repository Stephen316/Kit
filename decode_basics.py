"""Experimental named-feature and parameter-reference decoding for Fusion.

Layouts are inferred from Fusion 2705.1.30 samples, not a complete schema.
Unknown fields remain unknown; only basic sketch geometry is interpreted, with
no body topology or file writing provided.
"""

import argparse
from bisect import bisect_right
import json
from pathlib import Path
import re
import struct

from decode_parameters import decode_stream, read_string
from decode_sketch import decode_sketches
from decode_modeling import decode_modeling
from decode_placement import decode_placement
from decode_selection import decode_selections
from decode_tools import decode_tools
from fusion_archive import read_members
from fusion_records import Record, record_fragments
from fusion_metadata import design_records
from discover_features import discover_features
from decode_construction import decode_construction
from decode_profiles import decode_profiles
from decode_timeline import decode_timeline
from decode_assembly import decode_assembly
from decode_dependencies import decode_dependencies


def named_features(data, records):
    features = []
    starts = [r.start for r in records]
    labels = {"Sketch": "Sketch", "Extrude": "Extrude", "Revolve": "Revolve",
              "Fillet": "Fillet", "Chamfer": "Chamfer", "Shell": "Shell", "Hole": "Hole",
              "R-Pattern": "RectangularPattern", "Mirror": "Mirror", "Scale": "Scale",
              "WorkPlane": "ConstructionPlane", "Sweep": "Sweep", "Loft": "Loft",
              "C-Pattern": "CircularPattern", "Combine": "Combine", "Draft": "Draft",
              "Split": "SplitBody", "Move": "Move", "Thicken": "Thicken",
              "WorkAxis": "ConstructionAxis", "WorkPoint": "ConstructionPoint"}
    for label, kind in labels.items():
        marker = struct.pack("<I", len(label)) + label.encode("utf-16le")
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
                    "native_kind_label": label,
                    "stored_index": stored_index, "record_offset": record.start,
                    "type_code": record.type_code, "parameters": [],
                    "class_guid": record.class_guid, "class_namespace": record.class_namespace,
                }
                if kind != "Sketch":
                    name, _ = read_string(chunk, cursor + 8)
                    item["name"] = name or None
                else:
                    # The sketch feature points to a separate named sketch object.
                    # A counted list of parameter bindings precedes that pointer.
                    count = struct.unpack_from("<I", chunk, 3)[0]
                    root_offset = 13 + count * 11
                    if count > 1024 or root_offset + 8 > len(chunk) or chunk[root_offset - 1] != 1:
                        continue
                    root_id = struct.unpack_from("<Q", chunk, root_offset)[0]
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
        if len(body) not in (82, 85) or body[:6] != b"\x01\x01\0\0\0\x01":
            continue
        owner = struct.unpack_from("<Q", body, 6)[0]
        parameter_offset = 30 if len(body) == 85 else 27
        if body[parameter_offset - 1] != 1 or body[-11] != 1 or body[-2:] != b"\0\0":
            continue
        if struct.unpack_from("<Q", body, len(body) - 10)[0] != owner:
            continue
        parameter_id = struct.unpack_from("<Q", body, parameter_offset)[0]
        choices = pending.get(parameter_id, [])
        if owner not in by_id or len(choices) != 1:
            continue
        parameter = choices[0]
        if parameter.get("declared_binding_object_id", record.object_id) != record.object_id:
            continue
        raw_value = data[parameter["value_offset"]:parameter["value_offset"] + 8]
        if len(body) == 85:
            matches_value = body[21:29] == raw_value
        else:
            matches_value = body[21] == 1 and struct.unpack_from("<I", body, 22)[0] == parameter["raw_float64"]
        if not matches_value or parameter["role_offset"] in attached:
            continue
        by_id[owner]["parameters"].append({
            **parameter, "parameter_object_id": parameter_id,
            "binding_object_id": record.object_id, "binding_offset": record.start,
            "binding_value_representation": "float64" if len(body) == 85 else "tagged_uint32",
            "association": "explicit owner and parameter references with matching numeric payload",
        })
        attached.add(parameter["role_offset"])
    return [p for p in parameters if p["role_offset"] not in attached]


def sketch_references(data, records, features):
    by_feature = {f["object_id"]: f for f in features if f["kind"] in ("Extrude", "Revolve")}
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
    members = read_members(path, zstd_library)
    for name, data in members.items():
        if not name.endswith("FusionDesignSegmentType1/BulkStream.dat"):
            continue
        records, record_index = design_records(data, members.get(name.replace("BulkStream.dat", "MetaStream.dat")))
        features = named_features(data, records)
        discovery_summary = discover_features(data, records, features, record_index)
        parameters, rejected = decode_stream(data, records)
        unbound = attach_parameters(data, records, features, parameters)
        sketch_references(data, records, features)
        sketch_summary = decode_sketches(data, records, features)
        profile_summary = decode_profiles(data, records, features)
        modeling_summary = decode_modeling(data, records, features)
        placement_summary = decode_placement(data, records, features)
        construction_summary = decode_construction(data, records, features)
        selection_summary = decode_selections(data, records, features)
        tool_summary = decode_tools(data, records, features)
        timeline_summary = decode_timeline(data, records, features)
        assembly_summary = decode_assembly(data, records, features)
        dependency_summary = decode_dependencies(data, records, features, assembly_summary)
        resolved_selection_features = {s["feature_object_id"] for s in selection_summary["resolved"]}
        unresolved_selection_features = {s["feature_object_id"] for s in selection_summary["unresolved"]}
        modeling_summary["unresolved"] = [
            item for item in modeling_summary["unresolved"]
            if item["reason"] != "Referenced start/end geometry selection not decoded"
            or item["object_id"] not in resolved_selection_features-unresolved_selection_features]
        streams.append({
            "member": name, "features": features, "unbound_parameters": unbound,
            "rejected_parameters": rejected, "candidate_record_headers": len(records),
            "record_index": record_index,
            "feature_discovery": discovery_summary,
            "sketch_decoding": sketch_summary,
            "profile_decoding": profile_summary,
            "modeling_decoding": modeling_summary,
            "placement_decoding": placement_summary,
            "construction_decoding": construction_summary,
            "selection_decoding": selection_summary,
            "tool_decoding": tool_summary,
            "timeline_decoding": timeline_summary,
            "assembly_decoding": assembly_summary,
            "dependency_decoding": dependency_summary,
        })
    return {
        "file": str(path), "status": "experimental partial decoder",
        "scope": "Observed layouts in Fusion 2705.1.30; unsupported records remain undecoded",
        "limitations": [
            "Version-8 MetaStream indexes validate record boundaries; field semantics remain inferred from a small corpus.",
            "Type codes are local to the document and not treated as universal feature identifiers.",
            "Sketch support covers observed points, lines, circular/elliptical arcs, ellipses, NURBS, basic constraints and dimensions.",
            "Profile membership is partial; no general trimmed-contour reconstruction, topology, sketch solver or native writer.",
            "Only observed extrusion operation/extent fields and basic revolve parameters are decoded.",
            "No general feature history, suppression, all end conditions, arbitrary axis selection, or body reconstruction.",
        ],
        "streams": streams,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--zstd-library")
    args = parser.parse_args()
    print(json.dumps([decode_basics(p, args.zstd_library) for p in args.files], indent=2))
