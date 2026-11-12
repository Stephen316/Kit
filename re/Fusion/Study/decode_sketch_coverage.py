"""Account for observed sketch record families using metadata and explicit scope.

This is an audit of bounded class families, not a claim that every native sketch
record class is known. Unhandled dimensions/constraints retain unknown scope;
geometry candidates require an explicit owner that is a decoded sketch.
"""

import struct

from decode_sketch import attributes, constraint_prefix, reference

GEOMETRY_BASES = {"8E9D588C-28EF-43C4-B9A6-AA5430A68D4B", "EE518F9E-9CC3-4424-9CAB-2B92426E5312"}
CONSTRAINT = "60403D47-0C49-49B0-BDE8-1679608164A2"
DIMENSION = "0C3F3829-F0DB-4379-9479-CFEF71087971"
OFFSET = "afc07c10-99ac-5304-ae1b-dbee335b0e43"


def decode_sketch_coverage(data, records, features, record_index, sketch_summary):
    registry = {c["class_guid"]: c for c in record_index.get("class_registry", [])}
    if not registry:
        return {"status": "Unavailable without class registry", "unhandled": [],
                "limitations": ["No class-based coverage inference is made without metadata"]}
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    represented, geometry_owners = {}, {}
    for owner, sketch in sketches.items():
        for key in ("geometry", "constraints", "dimensions", "internal_associations", "texts"):
            for item in sketch.get(key, []):
                represented[item["object_id"]] = {"sketch_object_id": owner, "representation": key}
                if key == "geometry":
                    geometry_owners[item["object_id"]] = owner
                if key == "texts":
                    definition = item["definition"]
                    represented[definition["controller_object_id"]] = {
                        "sketch_object_id": owner, "representation": "ExplicitTextDefinitionSupport"}
                if item.get("kind") == "OffsetCurves":
                    for field in ("dimension_object_id", "relationship_object_id"):
                        represented[item[field]] = {"sketch_object_id": owner, "representation": "ExplicitOffsetSupport"}
    reasons = {}
    for key in ("unsupported_curves", "unsupported_dimensions", "unknown_constraint_codes"):
        for item in sketch_summary.get(key, []):
            reasons[item["object_id"]] = item.get("reason", "Unrecognized stored constraint code: "+str(item.get("code")))
    for item in sketch_summary.get("tool_constraints", {}).get("unresolved", []):
        reasons[item["object_id"]] = item["reason"]
    counts, accounted, unhandled = {}, {}, []
    for record in records:
        if not record.is_primary:
            continue
        lineage, guid = set(), record.class_guid
        while guid in registry and guid not in lineage:
            lineage.add(guid)
            guid = registry[guid]["base_class_guid"]
        body = data[record.body:record.end]
        owner = None
        if DIMENSION in lineage:
            family = "Dimension"
        elif CONSTRAINT in lineage or record.class_guid == OFFSET:
            family = "ConstraintOrRelationship"
        elif lineage & GEOMETRY_BASES:
            try:
                if body[:2] != b"\0\1":
                    continue
                props, _ = attributes(body, 2)
                owner = reference(body, len(body)-11)
                if "EntityGenesis" not in props or owner not in sketches:
                    continue
            except (ValueError, UnicodeError, IndexError, struct.error):
                continue
            family = "SketchOwnedGeometry"
        else:
            continue
        counts[family] = counts.get(family, 0)+1
        if record.object_id in represented:
            accounted[family] = accounted.get(family, 0)+1
            continue
        scope_reason = None
        if owner is None:
            try:
                inputs, _, cursor = constraint_prefix(body)
                scope_inputs = inputs[1:] if family == "Dimension" else inputs
                target_owners = {geometry_owners[i] for i in scope_inputs if i in geometry_owners}
                if scope_inputs and all(i in geometry_owners for i in scope_inputs) and len(target_owners) == 1:
                    owner = next(iter(target_owners))
                else:
                    if record.class_guid == "24DB790E-3DCD-4336-AFA3-6F119EF2239B" and body[cursor:cursor+3] == b"\0\1\1":
                        cursor += 3
                    candidate = reference(body, cursor)
                    if candidate in sketches:
                        owner = candidate
                    else:
                        scope_reason = "No decoded same-sketch argument set or direct sketch owner established"
            except (ValueError, UnicodeError, IndexError, struct.error) as error:
                scope_reason = str(error)
        unhandled.append({"object_id": record.object_id, "class_guid": record.class_guid,
                          "class_namespace": record.class_namespace, "record_offset": record.start,
                          "family": family, "sketch_object_id": owner,
                          "scope_status": "Explicit decoded sketch ownership/arguments" if owner in sketches else "Unresolved",
                          "scope_reason": scope_reason,
                          "reason": reasons.get(record.object_id, "Recognized record family has no decoded output or validated tool-support association")})
    return {"status": "Observed class-family accounting", "candidate_record_counts": counts,
            "accounted_record_counts": accounted, "unhandled": unhandled,
            "limitations": ["Counts are records, not API entity or user-constraint counts",
                            "Unknown class families, non-sketch-owned geometry and geometry with unreadable ownership are outside this audit",
                            "An empty unhandled list does not establish complete sketch decoding or regeneration"]}
