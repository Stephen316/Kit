"""Independent ByPoint ConstructionPoint definitions with owned vertex recipes.

Stored point geometry is a cache. Recipe framing establishes an explicit source
reference, not persistent ASM vertex/body identity or regenerated coordinates.
"""

import argparse
import copy
from dataclasses import replace
import json
from pathlib import Path
import struct
import uuid

from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference, same


FEATURE = "5F40832C-61AA-4A05-95B1-EFA0BA483138"
NATIVE = "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F"
BACKEND = "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44"
VERTEX_DESCRIPTOR = "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
RECIPE = "7ACC2A03-0261-4879-A14A-A93D661A5BDC"


def decode_construction_vertex_points(data, records, features):
    """Run after cached construction geometry/other definition passes.

    Attach only newly resolved vertex-source definitions to features. Existing
    definitions and known SketchPoint-source candidates are left unchanged.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Vertex-point typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    definitions, unresolved = [], []
    for feature in features:
        if feature["kind"] != "ConstructionPoint" or "construction_definition" in feature:
            continue
        source = primary.get(feature["object_id"])
        if source is None or source.class_guid != FEATURE:
            continue
        body = data[source.body:source.end]
        if len(body) < 33 or body[:3] != b"\0\0\1" or struct.unpack_from("<I", body, 3)[0] != 0:
            continue
        try:
            backend_id = reference(body, 22)
            _, backend = typed(backend_id, BACKEND)
            if len(backend) < 79 or struct.unpack_from("<I", backend, 47)[0] != 10:
                continue
            if (len(backend) != 178 or struct.unpack_from("<I", backend, 75)[0] != 1
                    or backend[:23] != b"\0"*23 or reference(backend, 167) != feature["object_id"]):
                raise ValueError("Unobserved vertex-point backend count/layout/owner")
            descriptor_id = reference(backend, 79)
            descriptor_record = primary.get(descriptor_id)
            if (descriptor_record is not None and descriptor_record.class_guid == "5A1BF548-241F-46FD-9FB5-E4B05126EB9D"
                    and descriptor_record.end-descriptor_record.body == 263):
                continue  # Existing SketchPoint-source definition branch.
            _, descriptor = typed(descriptor_id, VERTEX_DESCRIPTOR)
            if (len(descriptor) != 276 or descriptor[:4] != b"\0"*4
                    or struct.unpack_from("<I", descriptor, 15)[0] != 1
                    or reference(descriptor, 265) != feature["object_id"]):
                raise ValueError("Unobserved vertex-point descriptor count/layout/owner")
            namespace, cursor = read_string(descriptor, 19)
            identity, cursor = read_string(descriptor, cursor)
            for text in (namespace, identity):
                if len(text) != 36:
                    raise ValueError("Unsupported vertex-point descriptor UUID length")
                uuid.UUID(text)
            native_id = reference(body, 11)
            native_record, native = typed(native_id, NATIVE)
            if (source.start != feature["record_offset"] or body[7:11] != b"\0"*4
                    or native_id != feature.get("point_object_id") or feature["parameters"]
                    or native[:2] != b"\0\1"):
                raise ValueError("Vertex-point feature/native geometry reference mismatch")
            props, cursor = attributes(native, 2)
            if props != {"EntityGenesis": 0}:
                raise ValueError("Unsupported vertex-point native geometry attributes")
            position = numbers(native, cursor, 3)
            stored_tag, tag_end = read_string(native, cursor+24)
            if (stored_tag != "0_"+str(native_id) or reference(native, tag_end+20) != feature["object_id"]
                    or struct.unpack_from("<Q", native, tag_end+11)[0] != feature["stored_index"]
                    or native_record.start != feature["geometry_record_offset"]
                    or not same(position, feature["position_cm"])
                    or not same(position, numbers(backend, 23, 3))):
                raise ValueError("Vertex-point reciprocal native owner/index/cache mismatch")
            recipe_id = reference(descriptor, 4)
            recipe_record, _ = typed(recipe_id, RECIPE)
            recipe = decode_recipe(data, recipe_record, primary)
            if recipe["payload_kind"] != "vertex_recipe_data":
                raise ValueError("Vertex-point source recipe kind is not vertex_recipe_data")
            result = {"feature_object_id": feature["object_id"], "kind": "ConstructionPoint", "name": feature.get("name"),
                      "native_geometry_object_id": native_id, "backend_object_id": backend_id,
                      "definition_kind": "ByPoint", "api_definition_class": "ConstructionPointPointDefinition",
                      "source_kind": "VertexRecipe", "stored_feature_variant_code": 0, "stored_backend_method_code": 10,
                      "support_inputs": [{"role": "pointEntity", "descriptor_object_id": descriptor_id,
                                          "recipe_object_id": recipe_id, "namespace_text": namespace, "entity_guid_text": identity,
                                          "entity": {"kind": "VertexRecipe", "recipe": recipe},
                                          "association": "Explicit owned typed descriptor and bounded vertex_recipe_data reference; persistent topology identity unresolved"}],
                      "cached_geometry": {"position_cm": position},
                      "cache_consistency": {"native_backend_and_feature_positions_match": True,
                                            "source_recipe_geometry_validation": "Unresolved; recipe was not evaluated into topology or a position"},
                      "descriptor_payload_hex": descriptor.hex(), "backend_auxiliary_prefix_hex": backend[51:75].hex(),
                      "definition_evidence_scope": "Observed variant0/method10 and actual API ConstructionPointPointDefinition with BRepVertex source; native owned recipe framed independently of Loft",
                      "coordinate_scope": "Native parent component coordinates; occurrence/joint transforms not applied",
                      "geometry_status": "Cached construction-point geometry and explicit source recipe; persistent ASM vertex/body mapping and regeneration unresolved"}
            feature["construction_definition"] = result
            feature["decode_level"] = "Observed cached construction-point geometry and explicit owned vertex-source recipe"
            feature["selection_status"] = "Owned vertex recipe recovered; persistent topology identity unresolved"
            feature["unresolved_inputs"] = [item for item in feature.get("unresolved_inputs", [])
                                            if item != "Parametric construction input geometry references"]
            feature["unresolved_inputs"].append("Persistent source vertex identity and source-geometry reconstruction")
            definitions.append(result)
        except (ValueError, UnicodeError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "kind": "ConstructionPoint", "reason": str(error)})
    return {"definitions": definitions, "unresolved": unresolved,
            "scope": "Observed unresolved ByPoint vertex-source construction points only; owned recipe/cached geometry without persistent topology mapping"}


def validate_fixture(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root/"loftpointholdouts-bb91509a13e4"
    truth = json.loads((folder/"ground_truth.json").read_text())
    sample = next(s for s in truth["samples"] if s["case"] == "vertex_construction_sharp_end")
    assert not sample["getter_errors"] and not truth["errors"] and (folder/"complete.txt").is_file()
    archive = folder/sample["file"]
    main = decode_basics(archive, zstd_library)
    stream = next(s for s in main["streams"] if any(f["kind"] == "ConstructionPoint" for f in s["features"]))
    features = copy.deepcopy(stream["features"])
    # The fixture remains usable after this pass is integrated into decode_basics.
    point_feature = next(f for f in features if f["kind"] == "ConstructionPoint")
    point_feature.pop("construction_definition", None)
    members = read_members(archive, zstd_library)
    data = members[stream["member"]]
    records, _ = design_records(data, members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")))
    summary = decode_construction_vertex_points(data, records, features)
    assert len(summary["definitions"]) == 1 and not summary["unresolved"]
    result = summary["definitions"][0]
    api = next(s for s in sample["settings"]["sections"] if s["entity_type"] == "adsk::fusion::ConstructionPoint")
    checks = {"actual_parametric_point_name_matches": api["is_parametric"] and api["name"] == result["name"],
              "cached_position_matches_actual_point_getter": same(result["cached_geometry"]["position_cm"], api["world_point_cm"]),
              "actual_definition_class_matches": api["definition"]["entity_type"] == "adsk::fusion::"+result["api_definition_class"],
              "actual_definition_source_is_BRepVertex": api["definition"]["sources"]["pointEntity"]["entity_type"] == "adsk::fusion::BRepVertex",
              "native_source_is_bounded_vertex_recipe": result["support_inputs"][0]["entity"]["recipe"]["payload_kind"] == "vertex_recipe_data",
              "actual_source_vertex_position_independently_agrees_with_cache": same(api["definition"]["sources"]["pointEntity"]["world_point_cm"], result["cached_geometry"]["position_cm"]),
              "existing_definition_is_not_overwritten": decode_construction_vertex_points(data, records, features)["definitions"] == []}
    assert all(checks.values())
    report = {"api_version": truth["fusion_version"], "archive": str(archive.relative_to(root)), "checks": checks,
              "decoded": result, "actual_api_construction_point": api, "negative_checks": [],
              "interface": "decode_construction_vertex_points(data, records, features); run after construction geometry and other definition passes; attaches only unresolved vertex-source candidates",
              "integration": "Merge returned definitions into construction summary and remove prior unresolved entries only for successful feature IDs; keep persistent source-vertex uncertainty",
              "validation_command": "python3 decode_construction_vertex_points.py --validate --zstd-library <local libzstd path>"}
    descriptor_id = result["support_inputs"][0]["descriptor_object_id"]
    descriptor = next(r for r in records if r.is_primary and r.object_id == descriptor_id)
    native = next(r for r in records if r.is_primary and r.object_id == result["native_geometry_object_id"])
    native_body = data[native.body:native.end]
    _, cursor = attributes(native_body, 2)
    _, tag_end = read_string(native_body, cursor+24)
    recipe_id = result["support_inputs"][0]["recipe_object_id"]
    recipe = next(r for r in records if r.is_primary and r.object_id == recipe_id)
    kind_offset = data.index(b"vertex_recipe_data", recipe.body, recipe.end)
    for label, offset, replacement in (("Descriptor owner changed", descriptor.body+266, struct.pack("<Q", result["native_geometry_object_id"])),
                                        ("Native reciprocal feature owner changed", native.body+tag_end+21, struct.pack("<Q", result["backend_object_id"])),
                                        ("Recipe kind changed", kind_offset, b"foobar_recipe_data")):
        corrupted = bytearray(data)
        corrupted[offset:offset+len(replacement)] = replacement
        candidate = copy.deepcopy(stream["features"])
        next(f for f in candidate if f["kind"] == "ConstructionPoint").pop("construction_definition", None)
        rejected = decode_construction_vertex_points(bytes(corrupted), records, candidate)
        assert not rejected["definitions"] and len(rejected["unresolved"]) == 1, label
        report["negative_checks"].append({"check": label, "passed": True, "reason": rejected["unresolved"][0]["reason"]})
    altered_records = [replace(r, class_guid=BACKEND) if r.is_primary and r.object_id == recipe_id else r for r in records]
    candidate = copy.deepcopy(stream["features"])
    next(f for f in candidate if f["kind"] == "ConstructionPoint").pop("construction_definition", None)
    rejected = decode_construction_vertex_points(data, altered_records, candidate)
    assert not rejected["definitions"] and len(rejected["unresolved"]) == 1
    report["negative_checks"].append({"check": "Recipe reference wrong registered class rejected", "passed": True, "reason": rejected["unresolved"][0]["reason"]})
    report["limitations"] = ["One actual API vertex-source construction-point capture; other descriptor/backend layouts remain unsupported.",
                              "The source recipe and its numeric terms remain structurally framed; no persistent ASM vertex index, source-body identity, topology operation or coordinate derivation is inferred.",
                              "Cached geometry is checked independently against API construction-point and source-vertex getters in a root-component fixture; this does not create a general world-coordinate or assembly-solving claim.",
                              "Existing definition results and the known SketchPoint-source descriptor branch are preserved."]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("construction-vertex-point-decoding.json"))
    args = parser.parse_args()
    report = validate_fixture(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"definitions": 1, "negative_checks": len(report["negative_checks"]), "output": str(args.output)}))
