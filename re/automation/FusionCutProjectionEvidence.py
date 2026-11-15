import json

from FusionCutExtentEvidence import REVISION, design_members, p04_capture, record_site
from FusionCutFaceEvidence import body_members, inspect_face
from FusionCutJournalEvidence import feature_clocks, kernel_actor_join
from FusionCutSketchEvidence import historical_observations, inspect_sketches
from PairedCaptureIntake import require, sha256

from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_basics import named_features
from decode_brep import decode_topology
from decode_face_boundary_projections import decode_face_boundary_projections
from decode_pipe_recipe_incidence import decode_pipe_edge_recipe_operands
from decode_placement import transform_point
from decode_sketch import same
from fusion_metadata import design_records
from materialize_asm_literal_view import materialize_asm_literal_view


# the physical byte range remains tied to the qualified chart even when its dense indices change
def record_origin(blob, origins, index):
    origin = origins[index]
    start = origin["original_record_offset"]
    end = origin["original_record_end_offset"]
    return {**origin, "record_sha256": sha256(blob[start:end])}


# explicit named face and vertex incidence choose the edge before coordinates are consulted
def source_edge(relation, parsed, tags, face, graph, nodes, vertex_faces):
    recipe = relation["source"]["edge_recipe"]
    operands = decode_pipe_edge_recipe_operands(recipe, face_boundary_tail=True)
    naming = match_recipe_tag_names(recipe, tags, parsed=parsed)
    names = {}
    for entry in naming["name_entries"]:
        (candidate,) = entry["candidates"]
        require(
            candidate["owner_kind"] == "face"
            and candidate["body_graph_membership"] == [graph["body_index"]]
            and candidate["owner_record_index"] in graph["face_indices"],
            "P04 recipe operand is outside the qualified source BODY",
        )
        names[entry["name_table_index"]] = candidate["owner_record_index"]
    require(
        len(set(names.values())) == len(names) == 4,
        "P04 edge operand faces are ambiguous",
    )
    adjacent = {
        names[row["name_table_index"]] for row in operands["face_name_references"]
    }
    (incidence,) = [
        row
        for row in face["boundary_incidence"]
        if set(row["FACE_indices"]) == adjacent
    ]
    edge = nodes[incidence["edge_index"]]
    require(
        edge["kind"] == "edge"
        and nodes[edge["curve_index"]]["kind"] == "straight-curve",
        "P04 selected face incidence does not name a straight edge",
    )
    vertices = []
    for operand in operands["vertex_face_operands"]:
        faces = {
            names[row["name_table_index"]] for row in operand["face_name_references"]
        }
        (identity,) = [
            index for index, incident in vertex_faces.items() if incident == faces
        ]
        vertices.append(identity)
    require(
        len(set(vertices)) == 2
        and set(vertices) == set(incidence["stored_start_end_vertex_indices"]),
        "P04 projected recipe vertices do not exhaust the selected cap edge",
    )
    return edge, vertices, incidence, operands, naming


# existing archive evidence fixes both the selected cap and the independent sketch measurements
def inspect_projection(content, observed):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, _ = design_records(data, streams["MetaStream.dat"])
    features = named_features(data, records)
    by_id = {record.object_id: record for record in records if record.is_primary}
    cap = inspect_face(content, observed)
    selection = cap["native_face_recipe"]
    descriptor = selection["descriptor"]["object_id"]
    projections = decode_face_boundary_projections(
        data, records, features, marked_face_descriptors=(descriptor,)
    )
    require(
        len(projections["groups"]) == 1
        and len(projections["relationships"]) == 4
        and not projections["unresolved"],
        "P04 four-output projection route is unresolved",
    )
    (group,) = projections["groups"]
    require(
        group["source_descriptor_object_id"] == descriptor,
        "P04 projection did not choose the qualified support selector",
    )

    member = cap["native_body_mapping"]["history_blob_member"]
    blob = body_members(content)[member]
    native = feature_clocks(data, records, observed)
    journal = kernel_actor_join(blob, cap, native)
    earlier = journal["slot_zero_side_zero"]
    (binding,) = cap["native_body_mapping"]["bindings"]
    literal = materialize_asm_literal_view(blob)
    parsed = literal["view_parsed"]
    topology = decode_topology(parsed)
    (graph,) = topology["body_graphs"]
    require(
        not topology["unresolved"]
        and graph["body_transform_is_identity"]
        and graph["body_index"] == cap["literal_body_origin"]["view_record_index"],
        "P04 projected source BODY and clock-qualified face views disagree",
    )
    nodes = {row["index"]: row for row in topology["nodes"]}
    origins = {row["view_record_index"]: row for row in literal["origin_map"]}
    tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
    face = cap["selected_face"]
    vertex_faces = {}
    for identity in graph["coedge_indices"]:
        coedge = nodes[identity]
        face_id = nodes[coedge["loop_index"]]["face_index"]
        edge = nodes[coedge["edge_index"]]
        for key in ("start_vertex_index", "end_vertex_index"):
            vertex_faces.setdefault(edge[key], set()).add(face_id)

    (sketch,) = [
        row
        for row in inspect_sketches(content, observed)["sketches"]
        if row["sketch_record"]["object_id"] == group["target_sketch_object_id"]
    ]
    (history,) = [row for row in observed["sketches"] if row["name"] == sketch["name"]]
    measured = {row["index"]: row for row in history["curves"] if row["reference"]}
    require(len(measured) == 4, "P04 historical projection-line inventory differs")
    lines = {
        row["object_id"]: row
        for row in sketch["geometry"]
        if row.get("historical_curve_index") in measured
    }
    matrix = cap["document_frames"]["sketch_frames"][sketch["name"]][
        "sketch_to_world_matrix"
    ]
    root = cap["document_frames"]["root_occurrence"]["local_transform"]

    edges, outputs, witnesses = set(), set(), []
    for relation in projections["relationships"]:
        source = relation["source"]
        output = relation["output_cache"]
        identity = output["object_id"]
        require(
            relation["source_proxy_object_id"] == selection["proxy"]["object_id"]
            and relation["target_feature_object_id"] == selection["owner_object_id"]
            and source["face_recipe_object_id"] == selection["recipe"]["object_id"]
            and source["body_anchor_object_id"] == selection["body_anchor_object_id"]
            and source["native_body_object_id"] == binding["native_body_object_id"]
            and source["source_owner_object_id"] == earlier["actor"]["object_id"]
            and identity in lines,
            "P04 projected output did not originate from the clock-qualified cap selection",
        )
        edge, vertices, incidence, operands, naming = source_edge(
            relation, parsed, tags, face, graph, nodes, vertex_faces
        )
        outputs.add(identity)
        edges.add(edge["index"])
        measurement = measured[lines[identity]["historical_curve_index"]]
        source_points = [nodes[nodes[index]["point_index"]] for index in vertices]
        source_mm = [
            [10 * value for value in transform_point(root, point["raw_origin"])]
            for point in source_points
        ]
        output_mm = [
            [10 * value for value in transform_point(matrix, output[key])]
            for key in ("start_cm", "end_cm")
        ]
        observed_mm = [measurement[key] for key in ("start_world_mm", "end_world_mm")]
        require(
            all(
                same(a, b) and same(b, c)
                for a, b, c in zip(source_mm, output_mm, observed_mm, strict=True)
            ),
            "P04 exact source edge recipe disagrees with directed projected endpoints",
        )
        witnesses.append(
            {
                "projection": relation,
                "source_edge": record_origin(blob, origins, edge["index"]),
                "source_vertices_in_recipe_order": [
                    record_origin(blob, origins, index) for index in vertices
                ],
                "source_cap_incidence": incidence,
                "recipe_operands": operands,
                "recipe_face_names": naming,
                "projected_output_record": record_site(data, by_id[identity]),
                "historical_reference_line": measurement,
                "source_endpoints_world_mm": source_mm,
                "projected_endpoints_world_mm": output_mm,
            }
        )
    require(
        outputs == set(lines)
        and edges == {row["edge_index"] for row in face["boundary_incidence"]}
        and len(edges) == len(outputs) == 4,
        "P04 projected loops and cap edge sets are not in bijection",
    )
    return {
        "design_members": members,
        "asm_history_member": {"path": member, **cap["brep_members"][member]},
        "source_body_actor": earlier["actor"],
        "source_timestamp": earlier["timestamp"],
        "source_cap": cap["literal_face_origin"],
        "projection_group": group,
        "projection_records": {
            key: record_site(data, by_id[group[key]])
            for key in (
                "controller_object_id",
                "entry_object_id",
                "source_descriptor_object_id",
            )
        },
        "edges": witnesses,
    }


# the paired capture supplies the only eligible sketch archives and historical API observations
def report():
    git, capture = p04_capture()
    measurement = capture["measurements"]
    content = git.blob(REVISION, measurement["path"])
    require(sha256(content) == measurement["sha256"], "P04 measurement digest differs")
    historical = historical_observations(
        capture, git.parse_document(content, measurement["path"])
    )
    archives = []
    for source in capture["native_files"]:
        phase, observed = historical[source["variant"]]
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                **inspect_projection(git.blob(REVISION, source["path"]), observed),
            }
        )
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "receipt": capture["receipt"],
        "measurements": measurement,
        "archives": archives,
        "scope": "Exact saved projection recipe to original boss-cap ASM edge in the qualified literal chart; persistent API identities and regeneration remain open",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
