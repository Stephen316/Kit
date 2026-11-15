import io
import json
import math
import zipfile

from FusionCutExtentEvidence import (
    DESIGN,
    MEMBER_LIMIT,
    REVISION,
    design_members,
    inspect_archive,
    p04_capture,
    record_site,
)
from FusionCutSketchEvidence import historical_observations
from PairedCaptureIntake import require, sha256

from asm_records import inspect_asm, inspect_asm_members
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_assembly import decode_assembly
from decode_basics import named_features
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_bindings import decode_body_bindings
from decode_body_property_variants import decode_body_collection_attribute_variants
from decode_brep import decode_topology
from decode_occurrence_gate_attributes import occurrence_with_gate_attributes
from decode_placement import decode_placement, transform_point, transform_vector
from decode_recipe_components import decode_counted_recipe
from decode_shell_reconstruction import resolve_bounded_face_operands
from decode_sketch import same
from fusion_metadata import design_records
from materialize_asm_literal_view import materialize_asm_literal_view


# same asset scope protects the historical reference from interchangeable body charts
def body_members(content):
    members = {}
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for info in archive.infolist():
            path = info.filename
            if not path.startswith("FusionAssetName[Active]/Breps.BlobParts/BREP."):
                continue
            if not path.endswith((".smb", ".smbh")):
                continue
            require(
                path not in members and 0 < info.file_size <= MEMBER_LIMIT,
                "invalid duplicate or oversized active P04 BRep member",
            )
            with archive.open(info) as stream:
                members[path] = stream.read(MEMBER_LIMIT + 1)
            require(
                len(members[path]) == info.file_size,
                "P04 BRep member size differs from the ZIP index",
            )
    require(
        len(members) == 2 and sum(path.endswith(".smbh") for path in members) == 1,
        "unexpected active P04 BRep roster",
    )
    return members


# the common component frame lets independent geometry corroborate the recipe selected occurrence
def compare_plane(
    face_id, graph, nodes, plane_matrix, profile_matrix, depth, historical
):
    face = nodes[face_id]
    surface = nodes[face["surface_index"]]["analytic_surface"]
    require(
        surface["kind"] == "Plane" and not face["is_reversed"],
        "P04 source face plane or sense differs",
    )
    origin = transform_point(plane_matrix, (0, 0, 0))
    x_axis = transform_vector(plane_matrix, (1, 0, 0))
    y_axis = transform_vector(plane_matrix, (0, 1, 0))
    normal = transform_vector(plane_matrix, (0, 0, 1))
    require(
        historical["support"] == "BRepFace"
        and same(surface["normal"], normal)
        and same(surface["stored_reference_axis"], x_axis)
        and same(historical["x_direction"], x_axis)
        and same(historical["y_direction"], y_axis)
        and same(historical["origin_world_mm"], [10 * value for value in origin]),
        "P04 recipe selected plane, sketch matrix and historical frame disagree",
    )
    offset = math.sumprod(normal, origin)
    require(
        math.isclose(offset, math.sumprod(normal, surface["raw_origin"]), abs_tol=1e-9),
        "P04 recipe selected plane does not contain the cut sketch origin",
    )
    base_origin = transform_point(profile_matrix, (0, 0, 0))
    base_offset = math.sumprod(normal, base_origin)
    require(
        math.isclose(offset - base_offset, depth, abs_tol=1e-9) and depth > 0,
        "P04 supporting plane is not the positive boss cap at the bound boss depth",
    )

    other_faces = []
    for other_id in graph["face_indices"]:
        if other_id == face_id:
            continue
        other = nodes[other_id]
        other_plane = nodes[other["surface_index"]]["analytic_surface"]
        require(
            other_plane["kind"] == "Plane",
            "P04 source prism has an unexpected nonplanar face",
        )
        relation = math.sumprod(other_plane["normal"], normal)
        other_offset = math.sumprod(normal, other_plane["raw_origin"])
        if math.isclose(abs(relation), 1, abs_tol=1e-9):
            require(
                math.isclose(other_offset, base_offset, abs_tol=1e-9),
                "P04 opposite cap does not agree with the boss profile plane",
            )
            role = "opposite_cap_at_profile_plane"
        else:
            require(
                math.isclose(relation, 0, abs_tol=1e-9),
                "P04 other face is neither a side nor opposite cap",
            )
            role = "orthogonal_side"
        other_faces.append(
            {
                "face_record_index": other_id,
                "role": role,
                "face_is_reversed": other["is_reversed"],
                "surface": other_plane,
            }
        )
    require(
        sum(row["role"] == "opposite_cap_at_profile_plane" for row in other_faces) == 1
        and len(other_faces) == 5,
        "P04 support contrast requires one opposite cap and four sides",
    )
    return {
        "selected_surface": surface,
        "selected_face_is_reversed": face["is_reversed"],
        "component_sketch_origin_cm": origin,
        "component_normal": normal,
        "component_plane_offset_cm": offset,
        "boss_profile_plane_offset_cm": base_offset,
        "boss_depth_cm": depth,
        "other_faces": other_faces,
    }


# the initial result shares names but cannot substitute for the full source face recipe
def reject_initial_result(blob, parsed, recipe, body_index):
    topology = decode_topology(parsed)
    (graph,) = [
        row for row in topology["body_graphs"] if row["body_index"] == body_index
    ]
    nodes = {row["index"]: row for row in topology["nodes"]}
    tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
    names = match_recipe_tag_names(recipe, tags, parsed=parsed)
    try:
        resolve_bounded_face_operands(recipe, parsed, graph, nodes, tags)
    except ValueError as error:
        require(
            str(error)
            == "Shell reconstruction recipe boundary does not exhaust selected source FACE loop",
            "P04 initial result did not reach the expected boundary incidence refusal",
        )
        return {
            "status": "refused",
            "reason": str(error),
            "complete_name_correspondences": names["name_entries"],
        }
    raise ValueError(
        "P04 source-face recipe incorrectly passed in the initial result geometry"
    )


# source face identity starts at the owned recipe and ends in one typed literal body view
def inspect_face(content, historical):
    extent = inspect_archive(content)
    saved = extent["selection_routes"]
    streams, members_evidence = design_members(content)
    data = streams["BulkStream.dat"]
    records, _ = design_records(data, streams["MetaStream.dat"])
    primary = {row.object_id: row for row in records if row.is_primary}
    require(
        len(primary) == sum(row.is_primary for row in records),
        "ambiguous primary P04 record",
    )
    body_id = saved["historical_body"]["object_id"]
    recipe_id = saved["cut_sketch_face_selection"]["recipe"]["object_id"]
    recipe = decode_counted_recipe(data, primary[recipe_id])

    members = body_members(content)
    asm = inspect_asm_members(members)
    design_member = DESIGN + "BulkStream.dat"
    mappings = decode_body_bindings(data, records, design_member, asm)
    joined = decode_body_asm_identifiers(
        data, records, design_member, members, mappings
    )
    (mapping,) = joined["decoded"]
    (binding,) = mapping["bindings"]
    require(
        binding["native_body_object_id"] == body_id and not joined["unresolved"],
        "P04 body map differs",
    )
    blob_member = mapping["history_blob_member"]
    raw = members[blob_member]
    parsed = inspect_asm(raw)
    literal = materialize_asm_literal_view(
        raw, parsed=parsed, state_slot=0, pointer_side=0
    )
    (alias,) = [
        row
        for row in literal["literal_pair_aliases"]
        if row["kind"] == "body"
        and row["side1_inspection_record_index"] == binding["asm_body_index"]
    ]
    (body_origin,) = [
        row
        for row in literal["origin_map"]
        if row["kind"] == "body"
        and row["inspection_record_index"] == alias["side0_inspection_record_index"]
    ]
    view = literal["view_parsed"]
    topology = decode_topology(view)
    (graph,) = topology["body_graphs"]
    nodes = {row["index"]: row for row in topology["nodes"]}
    require(
        not topology["unresolved"]
        and graph["body_index"] == body_origin["view_record_index"]
        and nodes[graph["body_index"]]["stored_entity_id"] == binding["stored_handle"]
        and graph["body_transform_is_identity"]
        and graph["counts"]["face"] == graph["counts"]["loop"] == 6,
        "P04 literal source prism or identity transform differs",
    )
    tags = decode_asm_generic_tags(raw, parsed=view, allow_fpm_tracking=True)
    operand = resolve_bounded_face_operands(recipe, view, graph, nodes, tags)
    face_id = operand["selected_literal_FACE_index"]
    (face_origin,) = [
        row for row in literal["origin_map"] if row["view_record_index"] == face_id
    ]

    features = named_p04_sketches(data, records)
    assembly = decode_assembly(
        data, records, features, occurrence_decoder=occurrence_with_gate_attributes
    )
    properties = decode_body_collection_attribute_variants(data, records, assembly)
    (collection,) = [
        row
        for row in properties["decoded_collections"]
        if body_id in row["body_object_ids"]
    ]
    require(
        collection["object_id"] == mapping["owner_object_id"]
        and collection["mapping_record_object_id"]
        == mapping["mapping_record_object_id"]
        and all(
            feature["component_object_id"] == collection["component_object_id"]
            for feature in features
        ),
        "P04 sketch matrices and body collection do not share a native component",
    )
    profile, cut = features
    boss = extent["extrusions"]["NewBody"]["controls"]
    require(
        boss["start"]["kind"] == "ProfilePlane"
        and boss["extent"]["mode"] == "OneSided"
        and boss["extent"]["side_one"]["condition"] == "Distance",
        "P04 boss no longer has the positive profile plane contrast",
    )
    geometry = compare_plane(
        face_id,
        graph,
        nodes,
        cut["placement"]["sketch_to_component_matrix"],
        profile["placement"]["sketch_to_component_matrix"],
        boss["extent"]["side_one"]["distance_cm"],
        historical,
    )
    (alternate,) = [value for path, value in members.items() if path.endswith(".smb")]
    alternate_parsed = inspect_asm(alternate)
    alternate_tags = decode_asm_generic_tags(
        alternate, parsed=alternate_parsed, allow_fpm_tracking=True
    )
    alternate_matches = match_recipe_tag_names(
        recipe, alternate_tags, parsed=alternate_parsed
    )["name_entries"]
    selected_group = operand["operands"]["face_name_index"]
    require(
        alternate_matches[selected_group]["candidate_count"] > 1,
        "P04 alternate companion blob lacks the expected source name collision",
    )
    return {
        "design_members": members_evidence,
        "brep_members": {
            path: {"sha256": sha256(value), "size_bytes": len(value)}
            for path, value in members.items()
        },
        "native_face_recipe": saved["cut_sketch_face_selection"],
        "native_body_mapping": {
            **mapping,
            "native_record": record_site(
                data, primary[mapping["mapping_record_object_id"]]
            ),
        },
        "native_component_body_collection": collection,
        "native_sketch_placements": {
            feature["name"]: feature["placement"] for feature in features
        },
        "document_occurrence_diagnostics": assembly["unresolved"],
        "literal_body_alias": alias,
        "literal_body_origin": body_origin,
        "literal_face_origin": {
            **face_origin,
            "sha256": sha256(
                raw[
                    face_origin["original_record_offset"] : face_origin[
                        "original_record_end_offset"
                    ]
                ]
            ),
        },
        "selected_face": operand,
        "plane_corroboration": geometry,
        "initial_result_control": reject_initial_result(
            raw, parsed, recipe, binding["asm_body_index"]
        ),
        "unmapped_companion_name_control": alternate_matches[selected_group],
    }


# the named pair gives the independent support and boss profile frames
def named_p04_sketches(data, records):
    features = [row for row in named_features(data, records) if row["kind"] == "Sketch"]
    require(
        [row["name"] for row in features] == ["RectangleSketch", "CutSketch"],
        "unexpected P04 sketch roster",
    )
    placement = decode_placement(data, records, features)
    require(
        not placement["unresolved_sketches"], "P04 saved sketch placement unresolved"
    )
    return features


# the discovery receipt pins all byte sources while later licensed observations stay separate
def report():
    git, capture = p04_capture()
    path = capture["measurements"]["path"]
    receipt_bytes = git.blob(REVISION, path)
    require(
        sha256(receipt_bytes) == capture["measurements"]["sha256"],
        "P04 measurement digest differs",
    )
    historical = historical_observations(
        capture, git.parse_document(receipt_bytes, path)
    )
    archives = []
    for source in capture["native_files"]:
        phase, observation = historical[source["variant"]]
        (sketch,) = [
            row for row in observation["sketches"] if row["name"] == "CutSketch"
        ]
        archives.append(
            {
                "source": source,
                "observation": phase,
                **inspect_face(git.blob(REVISION, source["path"]), sketch),
            }
        )
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "receipt": capture["receipt"],
        "measurements": capture["measurements"],
        "archives": archives,
        "scope": "Named saved literal source-cap occurrence and component frame; native chronology and API identity remain open",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
