import io
import json
import struct
import sys
from collections import defaultdict
import zipfile
from pathlib import Path

from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256


ROOT = Path(__file__).resolve().parents[2]
REVISION = "89c25945f5833ad9c3a1c6c683df510b5702dd54"
SPECIFICATION = "re/automation/PairSpecs.json"
SPECIFICATION_SHA256 = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
RECEIPT = "re/automation/PairedCaptures/P04/fusion-9cf53a55ea8b/receipt.json"
RECEIPT_SHA256 = "8f0c62e6e12cca0b41e91009f929e5d8d823b8977d6344856e6c56a630e05080"
DESIGN = "FusionAssetName[Active]/FusionDesignSegmentType1/"
EXTRUDE_CLASS = "DD405BC2-D673-44F0-8833-5CB2A1C186C7"
MEMBER_LIMIT = 4 * 1024 * 1024

sys.path.insert(0, str(ROOT / "re/Fusion/Study"))
from decode_basics import attach_parameters, named_features, sketch_references
from decode_body_properties import BODY
from decode_body_selections import ANCHOR, CONTEXT, DESCRIPTOR, PROXY, SUPPORT, decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_extrude import decode_extrude
from decode_parameters import decode_stream
from decode_profiles import PROFILE_DESCRIPTOR_GUID
from decode_selection import native_proxy_references
from decode_selection_context_recipes import TOPOLOGY
from decode_selection_context_variants import EDGE_CONTEXT
from decode_sketch import reference
from fusion_metadata import design_records


def design_members(content):
    data, evidence = {}, {}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for leaf in ("BulkStream.dat", "MetaStream.dat"):
            path = DESIGN + leaf
            matching = [member for member in archive.infolist() if member.filename == path]
            require(len(matching) == 1, f"expected one active Design member {path}")
            member = matching[0]
            require(0 < member.file_size <= MEMBER_LIMIT, f"unexpected Design member size: {path}")
            with archive.open(member) as stream:
                body = stream.read(MEMBER_LIMIT + 1)
            require(len(body) == member.file_size, f"Design member size differs from ZIP index: {path}")
            data[leaf] = body
            evidence[leaf] = {"path": path, "size_bytes": len(body), "sha256": sha256(body)}
    return data, evidence


def record_site(data, record):
    return {
        "object_id": record.object_id,
        "class_guid": record.class_guid,
        "class_namespace": record.class_namespace,
        "record_offset": record.start,
        "record_end_offset": record.end,
        "decoded_body_offset": record.body,
        "record_sha256": sha256(data[record.start:record.end]),
        "primary": record.is_primary,
    }


def along_binding(data, parameter):
    offset = parameter["value_offset"]
    return {
        "parameter_name": parameter["parameter_name"],
        "parameter_object_id": parameter["parameter_object_id"],
        "binding_object_id": parameter["binding_object_id"],
        "binding_record_offset": parameter["binding_offset"],
        "value_offset": offset,
        "float64_le_hex": data[offset:offset + 8].hex(),
        "raw_value_cm": parameter["raw_float64"],
        "expression_candidates": parameter["expression_candidates"],
        "recorded_units": parameter["display_units"],
    }


# counted framing keeps adjacent markers from becoming independent selections
def counted_references(payload, offset, expected_count):
    require(struct.unpack_from("<I", payload, offset)[0] == expected_count,
            "unexpected P04 reference count")
    return [reference(payload, offset + 4 + 11 * index) for index in range(expected_count)]


# historical body provenance needs corroboration independent of the measured cut geometry
def inspect_selection_routes(data, records, features, cut, boss, end_proxy):
    """Follow only the observed selection layouts of the pinned discovery exports."""
    grouped = defaultdict(list)
    for record in records:
        if record.is_primary:
            grouped[record.object_id].append(record)
    primary = {identity: entries[0] for identity, entries in grouped.items() if len(entries) == 1}

    # record numbers can be reused across captures and must resolve within the current archive
    def typed(identity, class_guid):
        record = primary.get(identity)
        require(record is not None and record.class_guid == class_guid,
                f"absent, ambiguous or wrong-class P04 selection record {identity}")
        return record, data[record.body:record.end]

    # matching shape or a single pointer cannot establish ownership of a saved selection
    def route(proxy_id, owner, dependencies, face=False, end_selection=False):
        proxy, proxy_payload = typed(proxy_id, PROXY)
        descriptor_ids, attributes = native_proxy_references(data, proxy)
        require(not attributes and len(descriptor_ids) == 1 and len(proxy_payload) == 105,
                "unexpected P04 selection proxy framing")
        descriptor_id = descriptor_ids[0]
        require(reference(proxy_payload, 94) == owner
                and {proxy_id, descriptor_id}.issubset(dependencies),
                "P04 selection proxy owner or repeated dependency differs")
        descriptor, payload = typed(descriptor_id, TOPOLOGY if face else DESCRIPTOR)
        context_count_offset = 179 if face else 193
        context_count = 4 if face else int(end_selection)
        anchor_count_offset = context_count_offset + 4 + 11 * context_count
        trailer_offset = anchor_count_offset + 15
        require(len(payload) == trailer_offset + 67
                and payload[context_count_offset - 8:context_count_offset] == struct.pack("<Q", 2),
                "unexpected P04 selection descriptor framing")
        context_ids = counted_references(payload, context_count_offset, context_count)
        require(len(set(context_ids)) == context_count, "duplicate P04 descriptor context")
        for identity in context_ids:
            typed(identity, EDGE_CONTEXT if face else CONTEXT)
        anchor_id, = counted_references(payload, anchor_count_offset, 1)
        trailer = payload[trailer_offset:]
        require(trailer[14:18] == trailer[26:30] == b"\x04\x01\0\0"
                and trailer[41:44] == b"\x01\0\0" and trailer[55] == 0
                and reference(trailer, 56) == owner,
                "unexpected P04 selection descriptor trailer or owner")
        support_id = reference(trailer, 44)
        support, support_payload = typed(support_id, SUPPORT)
        source_offset = 12 if face else 96
        require(len(support_payload) == source_offset + 46
                and reference(support_payload, source_offset) == boss.object_id
                and reference(support_payload, source_offset + 19) == descriptor_id,
                "P04 descriptor support does not reciprocate the boss and descriptor")
        recipe_id = reference(payload, 4 if face else 18)
        recipe_record, _ = typed(recipe_id, RECIPE_GUID)
        recipe = decode_recipe(data, recipe_record, primary)
        expected_kind = "bounded_face_recipe_data" if face else "body_recipe_data"
        require(recipe["payload_kind"] == expected_kind, "unexpected P04 selection recipe kind")
        return {
            "proxy": record_site(data, proxy),
            "descriptor": record_site(data, descriptor),
            "support": record_site(data, support),
            "recipe": record_site(data, recipe_record),
            "recipe_payload_kind": expected_kind,
            "body_anchor_object_id": anchor_id,
            "context_object_ids": context_ids,
            "owner_object_id": owner,
            "stored_trailer_kind": struct.unpack_from("<I", trailer)[0],
        }

    anchors = decode_body_selections(data, records)["body_anchors"]
    require(len(anchors) == 1, "unexpected P04 historical body anchor count")
    anchor = anchors[0]
    anchor_record, _ = typed(anchor["object_id"], ANCHOR)
    body, _ = typed(anchor["native_body_object_id"], BODY)
    boss_payload = data[boss.body:boss.end]
    require(len(boss_payload) == 426 and reference(boss_payload, 151) == anchor_record.object_id
            and anchor["source_owner_object_id"] == boss.object_id,
            "P04 boss and historical body anchor disagree")

    # Common offsets come from the pinned Cut layout and its repeated reference list.
    cut_payload = data[cut.body:cut.end]
    require(len(cut_payload) == (467 if end_proxy is not None else 446),
            "unexpected P04 cut selection layout")
    body_proxy, = counted_references(cut_payload, 155, 1)
    cut_dependencies = counted_references(cut_payload, 249, 8 if end_proxy is not None else 7)
    body_selection = route(body_proxy, cut.object_id, cut_dependencies)
    end_selection = (route(end_proxy, cut.object_id, cut_dependencies, end_selection=True)
                     if end_proxy is not None else None)
    require(end_proxy is None or end_proxy != body_proxy, "P04 extent and cut body proxies overlap")

    profile_proxy, profile_payload = typed(reference(cut_payload, 132), PROXY)
    profile_ids, profile_attributes = native_proxy_references(data, profile_proxy)
    require(not profile_attributes and len(profile_ids) == 1 and len(profile_payload) == 105
            and reference(profile_payload, 94) == cut.object_id,
            "unexpected P04 cut profile proxy framing or owner")
    profile, _ = typed(profile_ids[0], PROFILE_DESCRIPTOR_GUID)
    require({profile_proxy.object_id, profile.object_id}.issubset(cut_dependencies),
            "P04 cut profile missing from its repeated dependencies")
    sketch_references(data, records, features)
    cut_feature, = [feature for feature in features if feature["record_offset"] == cut.start]
    sketch_reference, = cut_feature["sketch_reference_candidates"]
    require(sketch_reference["reference_record_offset"] == profile.start,
            "P04 sketch source does not match the owned cut profile descriptor")
    sketch, sketch_payload = typed(sketch_reference["feature_object_id"],
                                   "8DA771B7-52ED-42FC-94E2-2353FE141373")
    sketch_data, sketch_data_payload = typed(sketch_reference["sketch_object_id"],
                                             "44A64366-4BD3-4B24-881A-F94C206E8F2D")
    require(len(sketch_payload) == 425 and reference(sketch_payload, 56) == sketch_data.object_id
            and len(sketch_data_payload) == 231 and reference(sketch_data_payload, 216) == sketch.object_id
            and reference(sketch_data_payload, 204) == body.object_id,
            "P04 cut sketch feature, sketch data and historical body disagree")
    face_selection = route(reference(sketch_payload, 217), sketch.object_id,
                           counted_references(sketch_payload, 191, 12), face=True)
    selections = [body_selection, face_selection] + ([end_selection] if end_selection else [])
    require(all(selection["body_anchor_object_id"] == anchor_record.object_id for selection in selections),
            "P04 cut and sketch selections disagree on historical body")
    return {
        "scope": "Observed saved selection routes and historical body provenance",
        "historical_body": record_site(data, body),
        "historical_body_anchor": record_site(data, anchor_record),
        "historical_body_producer": record_site(data, boss),
        "cut_body_list_selection": body_selection,
        "cut_profile_proxy": record_site(data, profile_proxy),
        "cut_profile_descriptor": record_site(data, profile),
        "cut_sketch_feature": record_site(data, sketch),
        "cut_sketch_data": record_site(data, sketch_data),
        "cut_sketch_face_selection": face_selection,
        "end_field_selection": end_selection,
    }


# extent and selection observations must refer to the same indexed design streams
def inspect_archive(content):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, framing = design_records(data, streams["MetaStream.dat"])
    by_offset = {record.start: record for record in records}
    features = named_features(data, records)
    parameters, _ = decode_stream(data, records)
    attach_parameters(data, records, features, parameters)
    extrudes, extrusion_records = {}, {}
    for feature in features:
        if feature["kind"] != "Extrude":
            continue
        record = by_offset[feature["record_offset"]]
        require(record.is_primary and record.class_guid == EXTRUDE_CLASS, "unexpected extrusion class")
        observation, unresolved = decode_extrude(data[record.body:record.end], feature)
        operation = observation["operation"]["kind"]
        require(operation not in extrudes, f"ambiguous P04 operation: {operation}")
        extrusion_records[operation] = record
        reference = observation["extrusion_reference_fields"]["target"]
        reference_records = [
            record_site(data, candidate) for candidate in records if candidate.object_id == reference
        ]
        require(reference is None or sum(site["primary"] for site in reference_records) == 1,
                "end reference does not identify one primary object")
        extrudes[operation] = {
            "name": feature["name"],
            "record": record_site(data, record),
            "controls": observation,
            "decoder_unresolved": unresolved,
            "owned_along_distance": [
                along_binding(data, parameter) for parameter in feature["parameters"]
                if parameter["role"] == "AlongDistance"
            ],
            "end_reference_records": reference_records,
            "end_reference_semantics": "unresolved" if reference is not None else None,
        }
    require(set(extrudes) == {"Cut", "NewBody"}, "P04 must have one cut and one NewBody control")
    end_proxy = extrudes["Cut"]["controls"]["extrusion_reference_fields"]["target"]
    return {
        "design_members": members,
        "indexed_records": framing["indexed_records"],
        "extrusions": extrudes,
        "selection_routes": inspect_selection_routes(data, records, features, extrusion_records["Cut"],
                                                    extrusion_records["NewBody"], end_proxy),
    }


def report():
    git = GitSnapshot(ROOT)
    content = git.blob(REVISION, SPECIFICATION)
    require(sha256(content) == SPECIFICATION_SHA256, "paired specification digest differs")
    specification = git.parse_document(content, SPECIFICATION)
    recipes = [recipe for recipe in specification["recipes"] if recipe["id"] == "P04"]
    require(len(recipes) == 1 and recipes[0]["split"] == "discovery", "unexpected P04 evidence split")
    capture = inspect_capture(git, REVISION, RECEIPT, recipes[0], "fusion", specification, SPECIFICATION_SHA256)
    require(capture["receipt"]["sha256"] == RECEIPT_SHA256, "P04 capture receipt digest differs")
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "specification_sha256": SPECIFICATION_SHA256,
        "canonical_recipe_sha256": capture["canonical_recipe_sha256"],
        "receipt": capture["receipt"],
        "measurements": capture["measurements"],
        "authoring_provenance": capture["provenance"],
        "capture_qualification_blockers": capture["qualification_blockers"],
        "semantic_qualification": "unverified",
        "native_acceptance": "not_established",
        "archives": [
            {"source": row, **inspect_archive(git.blob(REVISION, row["path"]))}
            for row in capture["native_files"]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
