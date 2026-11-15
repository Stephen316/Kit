import json
import math

from FusionCutExtentEvidence import (
    REVISION,
    counted_references,
    design_members,
    p04_capture,
    record_site,
)
from FusionCutFaceEvidence import inspect_face
from FusionCutSketchEvidence import historical_observations, inspect_sketches
from PairedCaptureIntake import require, sha256

from decode_basics import named_features
from decode_expression_dependencies import derive_expression_dependencies
from decode_parameter_tables import decode_parameter_tables
from decode_parameters import decode_stream
from decode_placement import transform_point
from decode_sketch import reference, same
from decode_sketch_projections import decode_sketch_projections
from fusion_metadata import design_records


def origin_projection(data, records, features, primary, cut, frames):
    projections = decode_sketch_projections(
        data, records, features, allow_origin_points=True
    )
    (projection,) = [
        row
        for row in projections["relationships"]
        if row["target_feature_object_id"] == cut["feature_record"]["object_id"]
        and row["source"]["kind"] == "ConstructionPoint"
    ]
    source = projection["source"]
    output = projection["output_cache"]
    root = frames["root_occurrence"]
    component = primary[root["component_object_id"]]
    container = primary[source["origin_container_object_id"]]
    payload = data[container.body : container.end]
    require(
        container.class_guid == "2972A3B8-3627-49BC-8C3D-18707605EC44"
        and component.class_guid == "E03784ED-5E19-4E14-B9F2-3B07017018CD"
        and len(payload) == 96
        and reference(payload, 85) == component.object_id
        and reference(data[component.body : component.end], 66) == container.object_id,
        "P04 projected origin has no reciprocal root component ownership",
    )
    members = counted_references(payload, 4, 7)
    frame = frames["sketch_frames"][cut["name"]]
    require(
        len(set(members)) == 7
        and source["object_id"] in members
        and projection["target_sketch_object_id"] == cut["sketch_record"]["object_id"]
        and reference(data, frame["native_transform"]["record_end_offset"] - 11)
        == component.object_id
        and projection["method"] == "Project"
        and not projection["endpoint_progenitor_record_object_ids"],
        "P04 origin projection must name the root component and target its CutSketch",
    )
    source_cm = transform_point(root["local_transform"], source["position_cm"])
    matrix = frame["sketch_to_world_matrix"]
    normal = frames["selected_cap_world_normal"]
    signed_delta_cm = frames["selected_cap_signed_world_offset_mm"] / 10 - sum(
        a * b for a, b in zip(source_cm, normal, strict=True)
    )
    projected_cm = transform_point(matrix, output["position_cm"])
    require(
        same(
            projected_cm,
            [a + signed_delta_cm * b for a, b in zip(source_cm, normal, strict=True)],
        )
        and same([10 * x for x in projected_cm], frame["historical_origin_world_mm"]),
        "P04 projected point cache disagrees with the qualified support plane",
    )
    return {
        "projection": projection,
        "source_world_mm": [10 * x for x in source_cm],
        "projected_world_mm": [10 * x for x in projected_cm],
        "root_occurrence": frames["root_native_record"],
        "root_component": frames["root_component_record"],
        "sketch_placement": frame,
        "records": {
            key: record_site(data, primary[identity])
            for key, identity in {
                "controller": projection["controller_object_id"],
                "output_entry": projection["entry_object_id"],
                "source_proxy": projection["source_proxy_object_id"],
                "source_descriptor": projection["source_descriptor_object_id"],
                "descriptor_source_leaf": source["source_leaf_object_id"],
                "output_naming": projection["output_naming_record_object_id"],
                "output_naming_source_leaf": source[
                    "output_naming_source_leaf_object_id"
                ],
                "source_origin_point": source["object_id"],
                "source_origin_container": container.object_id,
                "projected_point": output["object_id"],
            }.items()
        },
    }


def center_bindings(data, records, primary, sketches, observed, projection):
    boss, cut = sketches["RectangleSketch"], sketches["CutSketch"]
    output = projection["projection"]["output_cache"]
    points = {
        row["object_id"]: row for row in cut["geometry"] if row["kind"] == "Point"
    }
    (midpoint,) = [row for row in cut["constraints"] if row["kind"] == "MidPoint"]
    point_id, line_id = midpoint["entity_ids"]
    center = points[point_id]
    origin = points[output["object_id"]]
    (diagonal,) = [row for row in cut["geometry"] if row["object_id"] == line_id]
    (history,) = [row for row in observed["sketches"] if row["name"] == "CutSketch"]
    (measured_diagonal,) = [
        row
        for row in history["curves"]
        if row["index"] == diagonal["historical_curve_index"]
    ]
    center_world_mm = [
        10 * value
        for value in transform_point(
            projection["sketch_placement"]["sketch_to_world_matrix"],
            center["position_cm"],
        )
    ]
    require(
        midpoint["dependency_entity_ids"] == [line_id, point_id]
        and diagonal["kind"] == "Line"
        and diagonal["is_construction"]
        and diagonal["entity_genesis"] == 2
        and origin["object_id"] != center["object_id"]
        and same(origin["position_cm"], output["position_cm"])
        and same(
            center["position_cm"], mean_point(diagonal["start_cm"], diagonal["end_cm"])
        )
        and measured_diagonal["construction"]
        and not measured_diagonal["reference"]
        and same(
            center_world_mm,
            mean_point(
                measured_diagonal["start_world_mm"], measured_diagonal["end_world_mm"]
            ),
        ),
        "P04 center does not match its saved constraint and historical construction diagonal",
    )

    parameters, refused = decode_stream(data, records)
    tables = decode_parameter_tables(data, records, parameters)
    expressions = derive_expression_dependencies(parameters, tables)
    require(
        not refused and not tables["unresolved"] and not expressions["unresolved"],
        "P04 reciprocal parameter collection or arithmetic expression refused",
    )
    (table,) = tables["decoded"]
    require(
        table["collection_owner_object_id"]
        == projection["root_component"]["object_id"],
        "P04 parameter collection is not owned by the root component",
    )
    native = {row["parameter_name"]: row for row in parameters}
    derived = {row["parameter_name"]: row for row in expressions["derived"]}
    historical = {row["name"]: row for row in observed["parameters"]}
    require(
        len(historical) == len(observed["parameters"]),
        "Duplicate historical Fusion parameter name",
    )

    witnesses = []
    for center_name, size_name in (
        ("cut_center_u_mm", "width_mm"),
        ("cut_center_v_mm", "height_mm"),
    ):
        (driver,) = [
            row for row in boss["dimensions"] if row["parameter_name"] == size_name
        ]
        (dimension,) = [
            row for row in cut["dimensions"] if row["parameter_name"] == center_name
        ]
        driver_parameter = native[size_name]
        parameter = native[center_name]
        proof = derived[center_name]
        driver_id = driver_parameter["parameter_object_id"]
        literal = f"{size_name} / 2"
        axis = {"Horizontal": 0, "Vertical": 1}[dimension["orientation"]]
        separation = center["position_cm"][axis] - origin["position_cm"][axis]
        require(
            driver["orientation"] == dimension["orientation"]
            and driver["is_driving"] is dimension["is_driving"] is True
            and dimension["entity_ids"] == [output["object_id"], point_id]
            and dimension["dependency_entity_ids"] == [point_id, output["object_id"]]
            and driver_parameter["declared_binding_object_id"]
            == driver["binding_object_id"]
            and parameter["declared_binding_object_id"]
            == dimension["binding_object_id"]
            and parameter["expression_candidates"] == [literal]
            and dimension["historical_dimension"]["expression"] == literal
            and proof["stored_expression"]
            == historical[center_name]["expression"]
            == literal
            and proof["referenced_parameter_object_ids"] == [driver_id]
            and proof["referenced_parameter_names"]
            == historical[center_name]["dependencies"]
            == [size_name]
            and historical[size_name]["dependents"] == [center_name]
            and math.isclose(
                driver_parameter["raw_float64"], historical[size_name]["value_internal"]
            )
            and all(
                math.isclose(value, driver_parameter["raw_float64"] / 2)
                for value in (
                    parameter["raw_float64"],
                    historical[center_name]["value_internal"],
                    abs(separation),
                )
            ),
            f"P04 saved and historical cut-center bindings disagree: {center_name}",
        )
        witnesses.append(
            {
                "stored_center_dimension": dimension,
                "stored_center_parameter": record_site(
                    data, primary[parameter["parameter_object_id"]]
                ),
                "stored_driver_dimension": driver,
                "stored_driver_parameter": record_site(data, primary[driver_id]),
                "expression_name_resolution": proof,
                "historical_driver_parameter": historical[size_name],
                "historical_center_parameter": historical[center_name],
                "signed_operand_separation_mm": 10 * separation,
            }
        )
    return {
        "midpoint_constraint": midpoint,
        "midpoint_point": center,
        "construction_diagonal": diagonal,
        "historical_construction_diagonal": measured_diagonal,
        "other_points_at_projected_origin": [
            row["record"]
            for identity, row in points.items()
            if identity != origin["object_id"]
            and same(row["position_cm"], origin["position_cm"])
        ],
        "center_world_mm": center_world_mm,
        "parameter_collection": record_site(
            data, primary[table["collection_object_id"]]
        ),
        "parameter_name_registry": record_site(
            data, primary[table["name_registry_object_id"]]
        ),
        "center_dimensions": witnesses,
    }


def mean_point(start, end):
    return [(a + b) / 2 for a, b in zip(start, end, strict=True)]


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
        archive = git.blob(REVISION, source["path"])
        streams, members = design_members(archive)
        data = streams["BulkStream.dat"]
        records, _ = design_records(data, streams["MetaStream.dat"])
        primary = {record.object_id: record for record in records if record.is_primary}
        features = named_features(data, records)
        sketches = {
            row["name"]: row for row in inspect_sketches(archive, observed)["sketches"]
        }
        frames = inspect_face(archive, observed)["document_frames"]
        projection = origin_projection(
            data, records, features, primary, sketches["CutSketch"], frames
        )
        bindings = center_bindings(
            data, records, primary, sketches, observed, projection
        )
        # only the width and height controls change the corresponding center parameter
        expected = {
            "edit-width_mm-44": [2.2, 1.0],
            "edit-height_mm-24": [2.0, 1.2],
        }.get(source["variant"], [2.0, 1.0])
        require(
            same(
                [
                    row["historical_center_parameter"]["value_internal"]
                    for row in bindings["center_dimensions"]
                ],
                expected,
            ),
            "P04 historical center parameter variant response disagrees",
        )
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                "historical_observation_label": observed["label"],
                "design_members": members,
                "origin_projection": projection,
                **bindings,
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
        "scope": "Saved native projection and dimension operands, reciprocal parameter names, and historical API expression and geometry controls",
        "limits": "Expression references derive from saved text and the reciprocal name registry. Independent serialized dependency edges and fresh API participant resolution remain open.",
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
