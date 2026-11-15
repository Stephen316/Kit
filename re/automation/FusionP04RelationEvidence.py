import json
import math

from FusionCutCenterEvidence import center_bindings, origin_projection
from FusionCutExtentEvidence import (
    REVISION,
    counted_references,
    design_members,
    p04_capture,
    record_site,
)
from FusionCutFaceEvidence import inspect_face
from FusionCutProfileEvidence import inspect_profiles
from FusionCutSketchEvidence import historical_observations, inspect_sketches
from PairedCaptureIntake import require, sha256

from decode_assembly import decode_assembly
from decode_basics import named_features
from decode_dependencies import decode_dependencies
from decode_parameters import decode_stream
from decode_sketch import reference, same
from fusion_metadata import design_records


def sketch_relation_lists(data, primary, sketch):
    definition = primary[sketch["sketch_record"]["object_id"]]
    owner = sketch["feature_record"]["object_id"]
    payload = data[definition.body : definition.end]
    dimensions = sketch["dimensions"]
    extent = {"RectangleSketch": 199, "CutSketch": 231}[sketch["name"]]
    require(
        definition.class_guid == "44A64366-4BD3-4B24-881A-F94C206E8F2D"
        and len(payload) == extent
        and payload[80] == payload[140] == 1
        and reference(payload, extent - 15) == owner,
        "P04 sketch relation and dimension list framing differs",
    )
    constraints = counted_references(payload, 81, 5)
    dimension_ids = counted_references(payload, 141, len(dimensions))
    require(
        constraints == [row["object_id"] for row in sketch["constraints"]]
        and dimension_ids == [row["object_id"] for row in dimensions],
        "P04 sketch-native lists do not exhaust parsed constraints and dimensions",
    )
    return {
        "definition_record": record_site(data, definition),
        "constraint_ids": constraints,
        "dimension_ids": dimension_ids,
    }


def rectangle_sides(sketch, profile, measured):
    perimeter = profile["region"]["stored_member_object_ids"]
    geometry = {row["object_id"]: row for row in sketch["geometry"]}
    history = {row["index"]: row for row in measured["curves"]}
    require(
        profile["source_sketch"] == sketch["sketch_record"] and len(perimeter) == 4,
        "P04 relation sketch does not own the selected four-line profile",
    )
    sides = {}
    for relation in sketch["constraints"]:
        kind = relation["kind"]
        if kind not in ("Horizontal", "Vertical"):
            continue
        (identity,) = relation["entity_ids"]
        line = geometry[identity]
        prior = history[line["historical_curve_index"]]
        fixed_axis = 1 if kind == "Horizontal" else 0
        world_delta = [
            end - start
            for start, end in zip(
                prior["start_world_mm"], prior["end_world_mm"], strict=True
            )
        ]
        opposite = measured[("x_direction", "y_direction")[fixed_axis]]
        require(
            identity in perimeter
            and identity not in sides
            and relation["dependency_entity_ids"] == [identity]
            and line["kind"] == "Line"
            and not prior["reference"]
            and not prior["construction"]
            and same([line["start_cm"][fixed_axis]], [line["end_cm"][fixed_axis]])
            and math.isclose(
                sum(a * b for a, b in zip(world_delta, opposite, strict=True)),
                0,
                abs_tol=1e-9,
            ),
            "P04 saved axis relation and measured authored side disagree",
        )
        sides[identity] = {
            "relation": relation,
            "saved_line": line,
            "historical_world_line": prior,
            "historical_length_mm": math.dist(
                prior["start_world_mm"], prior["end_world_mm"]
            ),
        }
    require(
        set(sides) == set(perimeter),
        "P04 axis relations do not cover the selected profile exactly once",
    )
    return sides


def size_dimensions(sketch, sides):
    names = {"width_mm", "height_mm"}
    if sketch["name"] == "CutSketch":
        names = {"cut_width_mm", "cut_height_mm"}
    results = {}
    for dimension in sketch["dimensions"]:
        name = dimension["parameter_name"]
        if name not in names:
            continue
        (side,) = [
            item
            for item in sides.values()
            if dimension["entity_ids"]
            == [item["saved_line"][key] for key in ("start_point_id", "end_point_id")]
        ]
        require(
            dimension["orientation"] == side["relation"]["kind"]
            and dimension["is_driving"] is True
            and same([dimension["value_mm"]], [side["historical_length_mm"]]),
            "P04 saved size dimension differs from the measured perimeter side",
        )
        results[name] = {
            "dimension": dimension,
            "line_record": side["saved_line"]["record"],
            "historical_curve_index": side["historical_world_line"]["index"],
            "historical_length_mm": side["historical_length_mm"],
        }
    require(set(results) == names, "P04 selected profile lacks both size dimensions")
    (corner,) = set.intersection(
        *(set(item["dimension"]["entity_ids"]) for item in results.values())
    )
    return results, corner


def corner_anchor(sketch, corner, measured, frames):
    (relation,) = [row for row in sketch["constraints"] if row["kind"] == "Coincident"]
    corner_id, anchor_id = relation["entity_ids"]
    point = {
        row["object_id"]: row for row in sketch["geometry"] if row["kind"] == "Point"
    }
    require(
        corner_id == corner
        and anchor_id != corner
        and relation["dependency_entity_ids"] == [anchor_id, corner]
        and len(sketch["geometry"]) == 9
        and len(point) == 5
        and all(
            anchor_id not in (row["start_point_id"], row["end_point_id"])
            for row in sketch["geometry"]
            if row["kind"] == "Line"
        )
        and all(
            same(point[identity]["position_cm"], [0, 0, 0])
            for identity in (corner, anchor_id)
        )
        and same(
            measured["origin_world_mm"],
            frames["sketch_frames"][sketch["name"]]["origin_world_mm"],
        ),
        "P04 boss origin relation does not name the distinct anchor and sized corner",
    )
    return {
        "relation": relation,
        "corner_record": point[corner]["record"],
        "separate_anchor_record": point[anchor_id]["record"],
        "historical_sketch_origin_world_mm": measured["origin_world_mm"],
    }


def dependency_graph_scope(data, records, primary, features, sketches):
    decoded = decode_dependencies(
        data, records, features, decode_assembly(data, records, features)
    )
    require(not decoded["unresolved"], "P04 document dependency graph is unresolved")
    (graph,) = decoded["graphs"]
    parameters, rejected = decode_stream(data, records)
    require(not rejected, "P04 parameter identities are unresolved")
    names = {row["parameter_name"]: row["parameter_object_id"] for row in parameters}
    expected = set()
    dimension_objects = set()
    parameter_objects = set()
    for sketch in sketches.values():
        owner = sketch["feature_record"]["object_id"]
        for dimension in sketch["dimensions"]:
            binding = dimension["binding_object_id"]
            expected.add((owner, binding, 1))
            dimension_objects.update((binding, dimension["object_id"]))
            parameter_objects.add(names[dimension["parameter_name"]])
    watched = parameter_objects | dimension_objects
    edges = [
        (row["object_id"], target["object_id"], target["stored_flags"])
        for row in graph["forward"]
        for target in row["edges"]
        if row["object_id"] in watched or target["object_id"] in watched
    ]
    require(
        set(edges) == expected and len(edges) == len(expected) == 6,
        "P04 dimension or parameter incidence changed in the document dependency graph",
    )
    return {
        "graph_record": record_site(data, primary[graph["object_id"]]),
        "graph_owner_record": record_site(data, primary[graph["owner_object_id"]]),
        "total_reciprocal_edges": graph["edge_count"],
        "parameter_ids_without_incident_edges": sorted(parameter_objects),
        "all_edges_incident_to_parameters_dimensions_or_bindings": sorted(edges),
    }


def inspect_relations(archive, observed):
    profile = inspect_profiles(archive, observed)
    sketches = {
        row["name"]: row for row in inspect_sketches(archive, observed)["sketches"]
    }
    frames = inspect_face(archive, observed)["document_frames"]
    streams, _ = design_members(archive)
    data = streams["BulkStream.dat"]
    records, _ = design_records(data, streams["MetaStream.dat"])
    primary = {record.object_id: record for record in records if record.is_primary}
    features = named_features(data, records)
    historical = {row["name"]: row for row in observed["sketches"]}

    rectangles = {}
    for name, operation in (("RectangleSketch", "NewBody"), ("CutSketch", "Cut")):
        sketch, measured = sketches[name], historical[name]
        selected = profile["profiles"][operation]
        sides = rectangle_sides(sketch, selected, measured)
        dimensions, corner = size_dimensions(sketch, sides)
        require(
            measured["fully_constrained"] and len(measured["constraints"]) == 5,
            "P04 historical rectangle has incomplete constraint coverage",
        )
        rectangles[name] = {
            **sketch_relation_lists(data, primary, sketch),
            "selected_feature": selected["journal_endpoint_actor"],
            "ordered_profile_edges": [
                sides[i] for i in selected["region"]["stored_member_object_ids"]
            ],
            "size_dimensions": dimensions,
            "size_dimension_corner_id": corner,
            "historical_constraint_types": [
                row["type"] for row in measured["constraints"]
            ],
        }

    boss = rectangles["RectangleSketch"]
    boss["corner_coincidence"] = corner_anchor(
        sketches["RectangleSketch"],
        boss["size_dimension_corner_id"],
        historical["RectangleSketch"],
        frames,
    )
    cut = rectangles["CutSketch"]
    projected = origin_projection(
        data, records, features, primary, sketches["CutSketch"], frames
    )
    center = center_bindings(data, records, primary, sketches, observed, projected)
    diagonal = center["construction_diagonal"]
    require(
        diagonal["object_id"]
        == profile["profiles"]["Cut"]["region"]["excluded_lines"][
            "construction_diagonal_object_id"
        ]
        and cut["size_dimension_corner_id"]
        in (diagonal["start_point_id"], diagonal["end_point_id"]),
        "P04 constrained diagonal does not span the selected rectangle and sized corner",
    )
    cut["construction_midpoint"] = {
        "relation": center["midpoint_constraint"],
        "diagonal_record": diagonal["record"],
        "projected_origin_record": projected["records"]["projected_point"],
        "midpoint_record": center["midpoint_point"]["record"],
        "center_dimensions": center["center_dimensions"],
    }
    return {
        "design_members": profile["design_members"],
        "rectangles": rectangles,
        "document_dependency_graph": dependency_graph_scope(
            data, records, primary, features, sketches
        ),
    }


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
                "historical_observation_label": observed["label"],
                **inspect_relations(git.blob(REVISION, source["path"]), observed),
            }
        )
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        **{
            key: capture[key]
            for key in (
                "recipe_id",
                "split",
                "application_build",
                "receipt",
                "measurements",
            )
        },
        "scope": "Saved sketch ownership, selected rectangle sides and participant lists with historical types, line geometry and parameter getter corroboration",
        "limits": "Historical measurements lack live relation and dimension participant getters. The audited document graph has no direct expression parameter edges.",
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
