"""Observed tangent-start and explicitly referenced ConstructionPoint Loft ends.

Native construction-point identities resolve by references, never by position.
Vertex-source recipe framing is retained without claiming persistent ASM mapping.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct
import uuid

from decode_brep_recipes import decode_recipe
from decode_loft_modes import SECTION_GUID, decode_loft_modes
from decode_loft_points import resolve_loft_point_section
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import attributes, numbers, reference, same


def resolve_loft_extended_point_section(data, records, section_id, feature, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Extended Loft point typed identity missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    _, section = typed(section_id, SECTION_GUID)
    if len(section) != 60 or struct.unpack_from("<I", section, 56)[0] != 5:
        result = resolve_loft_point_section(data, records, section_id, feature, features)
        if "point" in result:
            result["point"]["kind"] = "SketchPoint"
        return result
    owner_id = feature["object_id"]
    if (section[:6] != b"\0\0\1\0\0\0" or section[30:34] != b"\0"*4
            or reference(section, 34) != owner_id):
        raise ValueError("Unsupported ConstructionPoint Loft section prefix/owner")
    cached = numbers(section, 6, 3)
    selection_id = reference(section, 45)
    _, proxy = typed(selection_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    if len(proxy) != 105 or reference(proxy, 94) != owner_id:
        raise ValueError("ConstructionPoint Loft proxy owner/layout mismatch")
    proxy_record = primary[selection_id]
    descriptors, props = native_proxy_references(data, proxy_record)
    if props or len(descriptors) != 1:
        raise ValueError("Unsupported ConstructionPoint Loft proxy attributes/count")
    descriptor_id = descriptors[0]
    _, descriptor = typed(descriptor_id, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
    if (len(descriptor) != 263 or descriptor[:2] != b"\0\0"
            or struct.unpack_from("<I", descriptor, 13)[0] != 1
            or reference(descriptor, 252) != owner_id):
        raise ValueError("ConstructionPoint Loft descriptor count/owner/layout mismatch")
    namespace, cursor = read_string(descriptor, 17)
    entity_uuid, cursor = read_string(descriptor, cursor)
    for text in (namespace, entity_uuid):
        if len(text) != 36:
            raise ValueError("Unsupported ConstructionPoint Loft UUID field")
        uuid.UUID(text)
    if descriptor[cursor:cursor+12] != struct.pack("<QI", 2, 1):
        raise ValueError("Unsupported ConstructionPoint Loft context list")
    context_id = reference(descriptor, cursor+12)
    _, context = typed(context_id, "994C518A-A831-400A-B7C7-16DAC55F4F1C")
    if len(context) != 38:
        raise ValueError("Unobserved ConstructionPoint Loft context layout")
    leaf_id = reference(descriptor, 2)
    _, leaf = typed(leaf_id, "90055C05-546C-4EE7-B3C9-3DD922AD0C9C")
    if len(leaf) != 10 or leaf[:2] != b"\0\0":
        raise ValueError("Unsupported ConstructionPoint Loft native identity leaf")
    native_id = struct.unpack_from("<Q", leaf, 2)[0]
    _, native = typed(native_id, "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F")
    sources = [f for f in features if f["kind"] == "ConstructionPoint" and f.get("point_object_id") == native_id]
    if len(sources) != 1:
        raise ValueError("ConstructionPoint Loft source feature missing or ambiguous")
    source = sources[0]
    source_id = source["object_id"]
    source_record, source_body = typed(source_id, "5F40832C-61AA-4A05-95B1-EFA0BA483138")
    if (source_record.start != source["record_offset"] or source_body[:3] != b"\0\0\1"
            or source_body[7:11] != b"\0"*4 or reference(source_body, 11) != native_id):
        raise ValueError("ConstructionPoint Loft source/native reference mismatch")
    if native[:2] != b"\0\1":
        raise ValueError("Unobserved ConstructionPoint native geometry prefix")
    native_props, cursor = attributes(native, 2)
    if native_props != {"EntityGenesis": 0}:
        raise ValueError("Unobserved ConstructionPoint geometry attributes")
    position = numbers(native, cursor, 3)
    stored_tag, tag_end = read_string(native, cursor+24)
    if (stored_tag != "0_"+str(native_id) or reference(native, tag_end+20) != source_id
            or struct.unpack_from("<Q", native, tag_end+11)[0] != source["stored_index"]
            or not same(position, source["position_cm"]) or not same(position, cached)):
        raise ValueError("ConstructionPoint reciprocal geometry owner/index/position mismatch")

    def support(payload, offset, selected_source, support_owner, count):
        if (payload[offset+18:offset+22] != b"\1\1\0\0"
                or payload[offset+30:offset+34] != b"\1\1\0\0"
                or payload[offset+45:offset+48] != b"\1\0\0" or payload[offset+59] != 0):
            raise ValueError("Unobserved ConstructionPoint Loft selection trailer")
        numbers(payload, offset+22, 1)
        typed(reference(payload, offset+34), "5FBE538E-139B-46D4-BCAF-CC796D1E1F78")
        support_id = reference(payload, offset+48)
        _, chunk = typed(support_id, "6CCF41D5-40BE-48ED-A834-18F3EAED6C57")
        if (len(chunk) != 39+19*count or chunk[:12] != b"\0"*6+b"\1\1"+struct.pack("<I", count)
                or reference(chunk, 12) != selected_source or reference(chunk, 31) != support_owner
                or count == 2 and reference(chunk, 50) != support_owner or chunk[-8:] != b"\0"*8):
            raise ValueError("ConstructionPoint Loft support links are not reciprocal")
        return support_id

    proxy_support = support(proxy, 34, descriptor_id, selection_id, 1)
    descriptor_support = support(descriptor, 192, source_id, descriptor_id, 2)
    backend_id = reference(source_body, 22)
    _, backend = typed(backend_id, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44")
    if (backend[:23] != b"\0"*23 or not same(numbers(backend, 23, 3), position)
            or reference(backend, len(backend)-11) != source_id):
        raise ValueError("ConstructionPoint source backend owner/cache mismatch")
    variant, method, count = struct.unpack_from("<I", source_body, 3)[0], struct.unpack_from("<I", backend, 47)[0], struct.unpack_from("<I", backend, 75)[0]
    if len(backend) != 79+11*count+88:
        raise ValueError("ConstructionPoint source support list framing mismatch")
    support_ids = [reference(backend, 79+11*i) for i in range(count)]
    if (variant, method, count) == (2, 8, 3):
        definition = source.get("construction_definition", {})
        if (definition.get("definition_kind") != "ThreePlanes" or definition.get("backend_object_id") != backend_id
                or [s["descriptor_object_id"] for s in definition["support_inputs"]] != support_ids
                or not definition.get("support_consistency", {}).get("matches")):
            raise ValueError("ConstructionPoint three-plane source definition unresolved")
        source_definition = {"kind": "ThreePlanes", "backend_object_id": backend_id,
                             "support_descriptor_object_ids": support_ids,
                             "support_inputs": definition["support_inputs"], "support_consistency": definition["support_consistency"]}
    elif (variant, method, count) == (0, 10, 1):
        vertex_descriptor_id = support_ids[0]
        _, vertex_descriptor = typed(vertex_descriptor_id, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
        if (len(vertex_descriptor) != 276 or vertex_descriptor[:4] != b"\0"*4
                or struct.unpack_from("<I", vertex_descriptor, 15)[0] != 1
                or reference(vertex_descriptor, 265) != source_id):
            raise ValueError("Unobserved ConstructionPoint vertex descriptor owner/layout")
        recipe_id = reference(vertex_descriptor, 4)
        recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
        recipe = decode_recipe(data, recipe_record, primary)
        if recipe["payload_kind"] != "vertex_recipe_data":
            raise ValueError("ConstructionPoint vertex source has a different recipe kind")
        source_definition = {"kind": "ByPointVertexRecipe", "backend_object_id": backend_id,
                             "descriptor_object_id": vertex_descriptor_id, "recipe_object_id": recipe_id,
                             "recipe": recipe, "descriptor_payload_hex": vertex_descriptor.hex(),
                             "association_status": "Explicit owned vertex-recipe source framed; persistent ASM vertex identity and source-topology mapping unresolved"}
    else:
        raise ValueError("Uncaptured ConstructionPoint Loft source definition method")
    return {"point": {"kind": "ConstructionPoint", "selection_record_object_id": selection_id,
                      "descriptor_object_id": descriptor_id, "terminal_object_id": leaf_id,
                      "point_object_id": native_id, "construction_feature_object_id": source_id,
                      "name": source.get("name"), "component_position_cm": position,
                      "cached_section_position_cm": cached, "stored_section_kind": 5,
                      "proxy_support_record_object_id": proxy_support, "descriptor_support_record_object_id": descriptor_support,
                      "context_record_object_id": context_id, "context_payload_hex": context.hex(),
                      "context_status": "Observed typed context retained; frame/lifecycle semantics unresolved",
                      "source_definition": source_definition,
                      "association": "Owned section/proxy/descriptor -> typed native point identity -> reciprocal construction feature; descriptor support independently references that feature",
                      "coordinate_scope": "Native component; no occurrence or joint transforms applied"}}


def decode_loft_point_extensions(data, records, body, feature, features):
    result = decode_loft_modes(data, records, body, feature, features, allow_point_end_conditions=True,
                               section_resolver=resolve_loft_extended_point_section)
    if (result["operation"] != "NewBody" or not result["is_solid"] or result["is_closed"]
            or result["guide_count"] != 0 or result["section_count"] != 2):
        raise ValueError("Point extension requires open solid two-section NewBody Loft without guides")
    points = [s for s in result["sections"] if "point" in s]
    if len(points) != 1 or sum("profile" in s for s in result["sections"]) != 1:
        raise ValueError("Point extension requires exactly one point and one profile section")
    point_section = points[0]
    for section in result["sections"]:
        if "profile" in section and section["end_condition"]["type"] != "Free":
            raise ValueError("Point extension profile end must be Free")
    condition, point = point_section["end_condition"], point_section["point"]
    if point["kind"] == "SketchPoint":
        if point_section["index"] != 0 or condition["type"] != "PointTangent":
            raise ValueError("Sketch-point extension covers tangent START; use the original reader for earlier variants")
        if not math.isfinite(condition["weight"]) or condition["weight"] <= 0:
            raise ValueError("Tangent START weight must be positive and finite")
    elif condition["type"] != "PointSharp":
        raise ValueError("ConstructionPoint extension covers Sharp conditions only")
    elif point["source_definition"]["kind"] == "ByPointVertexRecipe" and point_section["index"] != 1:
        raise ValueError("Vertex-referenced ConstructionPoint extension covers END only")
    cursor = result["result_anchor_list_end_relative_offset"]
    if body[cursor:cursor+8] != b"\0"*8 or struct.unpack_from("<I", body, cursor+8)[0] != 36:
        raise ValueError("Unobserved point extension post-anchor input list")
    result.update(input_body_selection_record_object_ids=[], input_bodies=[], point_section_count=1,
                  point_scope="Observed SketchPoint tangent START with positive finite Start Weight, three-plane ConstructionPoint Sharp START/END and vertex-referenced ConstructionPoint Sharp END; source vertex topology remains partial",
                  section_selection_status="Explicit point/profile identities and reciprocal construction ownership; section positions cross-check selected geometry")
    return result


def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    fixtures = []
    for name, count in (("loftpointholdouts-bb91509a13e4", 4), ("loftpointholdouts-35b5ac0d2f42", 1)):
        folder = root/name
        truth = json.loads((folder/"ground_truth.json").read_text())
        assert (folder/"complete.txt").is_file() and not truth["errors"] and len(truth["samples"]) == count
        fixtures.extend((folder, sample) for sample in truth["samples"])
    report = {"api_version": truth["fusion_version"], "samples": [], "negative_checks": [],
              "interface": "decode_loft_point_extensions(data, records, body, feature, features); resolve_loft_extended_point_section is the existing five-argument section_resolver hook",
              "validation_command": "python3 decode_loft_point_extensions.py --validate --zstd-library <local libzstd path>"}
    start_weights = []
    for folder, sample in fixtures:
        assert not sample["getter_errors"]
        archive = folder/sample["file"]
        main = decode_basics(archive, zstd_library)
        stream = next(s for s in main["streams"] if any(f["kind"] == "Loft" for f in s["features"]))
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
        feature = next(f for f in stream["features"] if f["kind"] == "Loft")
        record = next(r for r in records if r.is_primary and r.object_id == feature["object_id"])
        settings = decode_loft_point_extensions(data, records, data[record.body:record.end], feature, stream["features"])
        selected = next(s for s in settings["sections"] if "point" in s)
        point, condition = selected["point"], selected["end_condition"]
        api = sample["settings"]["sections"][selected["index"]]
        checks = {"actual_point_entity_kind_matches": api["entity_type"] == "adsk::fusion::"+point["kind"],
                  "actual_point_position_matches_explicit_native_identity": same(point["component_position_cm"], api["world_point_cm"]),
                  "actual_end_condition_type_matches": api["end_condition_type"] == "adsk::fusion::Loft"+condition["type"]+"EndCondition",
                  "actual_controls_match": all(settings[k] == sample["settings"][k] for k in ("is_solid", "is_closed", "is_tangent_edges_merged", "section_count", "guide_count", "is_centerline"))}
        if condition["type"] == "PointTangent":
            actual_parameter_values = [p["value"] for p in sample["parameters"] if p["role"] == "Start Weight"]
            checks["actual_start_weight_matches"] = selected["index"] == 0 and condition["weight"] == api["weight"] and math.isfinite(api["weight"]) and api["weight"] > 0
            checks["explicit_start_weight_binding_matches_api_parameter_role"] = actual_parameter_values == [condition["weight"]]
            start_weights.append(condition["weight"])
            tangent_case = (data, records, record, feature, stream["features"], settings)
        else:
            source = point["source_definition"]
            checks["actual_parametric_point_and_name_match"] = api["is_parametric"] and api["name"] == point["name"]
            if source["kind"] == "ThreePlanes":
                checks["actual_source_definition_is_three_planes"] = api["definition"]["entity_type"] == "adsk::fusion::ConstructionPointThreePlanesDefinition"
                checks["actual_source_plane_names_match_explicit_native_refs"] = [s["entity"]["name"] for s in source["support_inputs"]] == [api["definition"]["sources"][k]["name"] for k in ("planeOne", "planeTwo", "planeThree")]
            else:
                checks["actual_source_is_vertex_referenced_construction_point"] = api["definition"]["entity_type"] == "adsk::fusion::ConstructionPointPointDefinition" and api["definition"]["sources"]["pointEntity"]["entity_type"] == "adsk::fusion::BRepVertex"
                checks["native_source_recipe_kind_is_vertex"] = source["recipe"]["payload_kind"] == "vertex_recipe_data"
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append({"archive": str(archive.relative_to(root)), "checks": checks,
                                   "decoded": settings, "actual_api_point_section": api,
                                   "actual_requested_source": sample["requested_point_source"],
                                   "coordinate_evidence_scope": "Root-component fixtures only; captured API world point equals native component point here"})
        if point["kind"] == "ConstructionPoint":
            baseline = data, records, feature, stream["features"], selected
    data, records, feature, features, selected = baseline
    point = selected["point"]
    for label, identity, delta, value in (("Loft descriptor owner mismatch", point["descriptor_object_id"], 253, struct.pack("<Q", point["construction_feature_object_id"])),
                                          ("Native point leaf replaced with unowned origin identity", point["terminal_object_id"], 2, struct.pack("<Q", 45)),
                                          ("Descriptor support source backlink mismatch", point["descriptor_support_record_object_id"], 13, struct.pack("<Q", feature["object_id"])),
                                          ("Section cached point disagrees with native geometry", selected["section_record_object_id"], 6, struct.pack("<d", 1.0))):
        record = next(r for r in records if r.is_primary and r.object_id == identity)
        corrupted = bytearray(data)
        corrupted[record.body+delta:record.body+delta+len(value)] = value
        try:
            resolve_loft_extended_point_section(bytes(corrupted), records, selected["section_record_object_id"], feature, features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    data, records, record, feature, features, settings = tangent_case
    weight_id = settings["start_condition"]["weight_binding_object_id"]
    for label, value in (("Zero tangent START weight rejected", 0.0), ("Negative tangent START weight rejected", -1.0), ("Nonfinite tangent START weight rejected", float("nan"))):
        changed = copy.deepcopy(feature)
        next(p for p in changed["parameters"] if p["binding_object_id"] == weight_id)["raw_float64"] = value
        try:
            decode_loft_point_extensions(data, records, data[record.body:record.end], changed, features)
        except ValueError as error:
            report["negative_checks"].append({"check": label, "passed": True, "reason": str(error)})
        else:
            raise AssertionError(label)
    assert sorted(start_weights) == [1.0, 2.0]
    report["start_weight_evidence"] = {"actual_api_getter_contrasts": sorted(start_weights), "binding_role": "Start Weight",
                                       "decoding_rule": "Positive finite numeric binding; no equality to fixture-specific values required"}
    report["limitations"] = ["The extension covers exactly one point plus one Free profile, open solid NewBody without guides. Three-plane ConstructionPoints support Sharp START/END, vertex-referenced ConstructionPoints support Sharp END only, and SketchPoint tangent START decodes positive finite Start Weight bindings.",
                              "ConstructionPoint identity follows the explicit native datum reference and reciprocal feature links; coordinate agreement never chooses an identity.",
                              "The vertex source is an owned, bounded vertex_recipe_data record; persistent ASM vertex identity, topology interpretation and source-body mapping remain unresolved.",
                              "Point contexts are retained as opaque typed bytes. No general assembly/world placement, joint solving or Loft regeneration is claimed."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("loft-point-extension-decoding.json"))
    args = parser.parse_args()
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"samples": len(report["samples"]), "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
