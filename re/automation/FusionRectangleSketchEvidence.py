import json
import math
import struct
from collections import Counter
from functools import partial
from uuid import UUID

from FusionCutExtentEvidence import (
    REVISION,
    ROOT,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    counted_references,
    design_members,
    record_site,
)
from FusionCutSketchEvidence import cache_witness, historical_observations, match_lines
from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256

from decode_assembly import OCCURRENCE_GUID, decode_assembly
from decode_basics import attach_parameters, named_features
from decode_dimension_annotations import decode_dimension_annotations
from decode_dimension_controls import decode_dimension_controls
from decode_occurrence_gate_attributes import occurrence_with_gate_attributes
from decode_parameters import decode_stream, read_string
from decode_placement import (
    IDENTITY,
    decode_placement,
    transform_point,
    transform_vector,
)
from decode_selection import native_origin_entities
from decode_sketch import decode_sketches, reference, same
from decode_sketch_coverage import decode_sketch_coverage
from fusion_metadata import design_records

# a local receipt pin protects the discovery controls from later archive substitutions
RECEIPT = "re/automation/PairedCaptures/P01/fusion-5dc3245eb59c/receipt.json"

# the receipt binds original historical measurements to all six source file digests
RECEIPT_SHA256 = "88ca575b5176e61cd25d585c9cb6804d6ea2c1b3d3ef843ac2d2bcb43593a4db"


# direct typed references distinguish the stored support identity from a plane fit
def origin_plane_route(data, records, primary, feature):

    # selecting a basis needs a typed target before geometry is compared
    def typed(identity, class_guid):
        record = primary[identity]
        require(
            record.class_guid == class_guid,
            "P01 native reference has the wrong primary class",
        )
        return record, data[record.body : record.end]

    sketch, native = typed(feature["object_id"], "8DA771B7-52ED-42FC-94E2-2353FE141373")
    definition, definition_bytes = typed(
        feature["sketch_object_id"], "44A64366-4BD3-4B24-881A-F94C206E8F2D"
    )
    require(
        len(native) == 293
        and len(definition_bytes) == 199
        and reference(native, 34) == definition.object_id
        and reference(definition_bytes, 184) == sketch.object_id,
        "P01 sketch owner copies disagree",
    )
    controller, controller_bytes = typed(
        reference(native, 45), "7B6C3C2D-4096-4E6D-B225-699E8C2D9355"
    )
    dependencies = counted_references(native, 147, 4)
    descriptor, payload = typed(dependencies[0], "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
    require(
        len(controller_bytes) in (187, 315)
        and counted_references(controller_bytes, len(controller_bytes) - 103, 1)
        == [descriptor.object_id]
        and reference(controller_bytes, len(controller_bytes) - 11) == sketch.object_id
        and dependencies[1] == controller.object_id,
        "P01 controller and sketch plane descriptor copies disagree",
    )
    require(
        len(payload) == 263
        and payload[:2] == bytes(2)
        and struct.unpack_from("<I", payload, 13)[0] == 1
        and reference(payload, 252) == sketch.object_id,
        "P01 plane descriptor framing or owner differs",
    )
    namespace, cursor = read_string(payload, 17)
    entity_namespace, cursor = read_string(payload, cursor)
    UUID(namespace)
    UUID(entity_namespace)
    require(cursor == 169, "P01 plane descriptor UUID framing differs")
    leaf, leaf_bytes = typed(
        reference(payload, 2), "90055C05-546C-4EE7-B3C9-3DD922AD0C9C"
    )
    require(
        len(leaf_bytes) == 10 and leaf_bytes[:2] == bytes(2),
        "P01 origin selection leaf framing differs",
    )
    (plane_id,) = struct.unpack_from("<Q", leaf_bytes, 2)
    plane_record, _ = typed(plane_id, "8D424E29-DE23-4B1F-A3AD-84C52A497D1A")
    plane = native_origin_entities(data, records)[plane_id]
    container, container_bytes = typed(
        plane["origin_container_object_id"], "2972A3B8-3627-49BC-8C3D-18707605EC44"
    )
    component, component_bytes = typed(
        feature["component_object_id"], "E03784ED-5E19-4E14-B9F2-3B07017018CD"
    )
    members = counted_references(container_bytes, 4, 7)
    require(
        len(container_bytes) == 96
        and len(set(members)) == 7
        and plane_id in members
        and reference(container_bytes, 85) == component.object_id
        and reference(component_bytes, 66) == container.object_id,
        "P01 plane container and sketch component disagree",
    )
    return {
        "plane": plane,
        "descriptor_namespace": namespace,
        "descriptor_entity_uuid": entity_namespace,
        "records": {
            label: record_site(data, record)
            for label, record in (
                ("sketch", sketch),
                ("definition", definition),
                ("controller", controller),
                ("descriptor", descriptor),
                ("leaf", leaf),
                ("plane", plane_record),
                ("origin_container", container),
                ("component", component),
            )
        },
    }


# exact saved participants and historical inventory are independent scope checks
def compare_sketch(
    data, records, index, features, historical, variant, *, measured_world_curves=None
):
    summary = decode_sketches(
        data, records, features, allow_reversed_point_dimensions=True
    )
    coverage = decode_sketch_coverage(data, records, features, index, summary)
    require(
        coverage["status"] == "Observed class-family accounting"
        and not coverage["unhandled"],
        "P01 sketch record inventory has unsupported candidates",
    )
    placement = decode_placement(data, records, features)
    require(
        not placement["unresolved_sketches"], "P01 saved sketch placement unresolved"
    )
    assembly = decode_assembly(
        data,
        records,
        features,
        occurrence_decoder=partial(
            occurrence_with_gate_attributes, allow_root_identity_marker=True
        ),
    )
    (root,) = assembly["native_occurrences"]
    (world,) = assembly["root_sketches"]
    (feature,) = features
    require(
        not assembly["unresolved"]
        and not assembly["occurrence_paths"]
        and root["local_transform"] == IDENTITY
        and root["component_object_id"] == feature["component_object_id"]
        and world["sketch_object_id"] == feature["sketch_object_id"],
        "P01 root and sketch frame chain is incomplete",
    )
    primary = {row.object_id: row for row in records if row.is_primary}
    require(
        len(primary) == sum(row.is_primary for row in records),
        "P01 primary identity is ambiguous",
    )
    root_record = primary[root["object_id"]]
    transform = primary[feature["placement"]["transform_object_id"]]
    require(
        root_record.class_guid == OCCURRENCE_GUID
        and root["stored_pre_uuid_marker"] == 1
        and transform.class_guid == "F47A46FB-DA27-4AFA-8A72-1B38FA596E23"
        and transform.start == feature["placement"]["record_offset"]
        and reference(data, transform.end - 11) == root["component_object_id"],
        "P01 typed root and transform provenance differ",
    )
    support = origin_plane_route(data, records, primary, feature)
    plane = support["plane"]
    matrix = world["sketch_to_world_matrix"]
    axes = [
        transform_vector(matrix, axis) for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    ]
    origin = [10 * value for value in transform_point(matrix, (0, 0, 0))]
    expected_plane = "YZ" if variant == "plane-yz" else "XY"
    require(
        plane["name"] == historical["plane"] == expected_plane
        and same(plane["normal"], historical["normal"])
        and same(plane["normal"], axes[2])
        and same(historical["x_direction"], axes[0])
        and same(historical["y_direction"], axes[1])
        and same(historical["origin_mm"], origin)
        and same(origin, [10 * value for value in plane["origin_cm"]]),
        "P01 saved plane or directed sketch axes differ from the historical API",
    )

    geometry = {item["object_id"]: item for item in feature["geometry"]}
    lines = [item for item in geometry.values() if item["kind"] == "Line"]
    points = [item for item in geometry.values() if item["kind"] == "Point"]
    require(
        len(points) == historical["point_count"] == 5
        and len(lines) == 4
        and len(geometry) == 9
        and not historical["other_curve_count"],
        "P01 rectangle geometry roster differs",
    )
    measured_curves = (
        historical_world_curves(historical)
        if measured_world_curves is None
        else measured_world_curves
    )
    line_indices = match_lines(
        lines,
        {
            "origin_world_mm": historical["origin_mm"],
            "x_direction": historical["x_direction"],
            "y_direction": historical["y_direction"],
            "curves": measured_curves,
        },
    )
    constraints = feature["constraints"]
    require(
        len(constraints) == 5
        and Counter(row["kind"] + "Constraint" for row in constraints)
        == Counter(row["type"] for row in historical["constraints"]),
        "P01 constraint inventory differs from the archived API",
    )
    profile_points = {
        line[key] for line in lines for key in ("start_point_id", "end_point_id")
    }
    relation_targets = {}
    for relation in constraints:
        if relation["kind"] == "Coincident":
            left, right = [geometry[identity] for identity in relation["entity_ids"]]
            require(
                left["kind"] == right["kind"] == "Point"
                and left["object_id"] != right["object_id"]
                and len({left["object_id"], right["object_id"]} & profile_points) == 1
                and same(left["position_cm"], right["position_cm"])
                and same(left["position_cm"], [0, 0, 0]),
                "P01 Coincident operands do not corroborate the origin anchor",
            )
            continue
        (identity,) = relation["entity_ids"]
        require(
            relation["kind"] in ("Horizontal", "Vertical")
            and identity in line_indices
            and identity not in relation_targets,
            "P01 axis relation lacks one uniquely matched line",
        )
        line = geometry[identity]
        perpendicular_axis = 1 if relation["kind"] == "Horizontal" else 0
        require(
            math.isclose(
                line["start_cm"][perpendicular_axis],
                line["end_cm"][perpendicular_axis],
                abs_tol=1e-9,
            ),
            "P01 explicit axis relation disagrees with its line geometry",
        )
        relation_targets[identity] = relation["kind"]
    require(
        set(relation_targets) == set(line_indices),
        "P01 profile has incomplete saved axis relations",
    )

    controls = decode_dimension_controls(data, records, features)
    require(not controls["unresolved"], "P01 saved dimension controls unresolved")
    annotations = decode_dimension_annotations(data, records, features, controls)
    caches = {row["object_id"]: row for row in annotations["decoded"]}
    refusals = {row["object_id"]: row for row in annotations["unresolved"]}
    observed_dimensions = {row["parameter"]: row for row in historical["dimensions"]}
    require(
        set(observed_dimensions) == {"width_mm", "height_mm"}
        and len(feature["dimensions"]) == 2,
        "P01 dimension roster differs",
    )
    dimensions = []
    for dimension in feature["dimensions"]:
        identity = dimension["object_id"]
        name = dimension["parameter_name"]
        observed = observed_dimensions[name]
        (line,) = [
            row
            for row in lines
            if {row["start_point_id"], row["end_point_id"]}
            == set(dimension["entity_ids"])
        ]
        require(
            observed["type"] == "SketchLinearDimension"
            and dimension["is_driving"] == observed["driving"]
            and observed["expression"] in dimension["expression_candidates"]
            and math.isclose(observed["value_mm"], dimension["value_mm"], abs_tol=1e-9)
            and dimension["orientation"] == relation_targets[line["object_id"]],
            "P01 saved point dimension differs",
        )
        dimensions.append(
            {
                **dimension,
                "ordered_operand_line_object_id": line["object_id"],
                "record": record_site(data, primary[identity]),
                "binding_record": record_site(
                    data, primary[dimension["binding_object_id"]]
                ),
                "historical_dimension": observed,
                "measurement_cache": cache_witness(
                    data, primary[identity], dimension, caches, refusals
                ),
            }
        )
    require(
        len(historical["profile_areas_mm2"]) == 1
        and historical["fully_constrained"]
        and math.isclose(
            historical["profile_areas_mm2"][0],
            math.prod(row["value_mm"] for row in observed_dimensions.values()),
        ),
        "P01 historical rectangle area does not match its native dimensions",
    )
    return {
        "support": support,
        "root_record": record_site(data, root_record),
        "root_occurrence": root,
        "transform_record": record_site(data, transform),
        "sketch_to_world_matrix": matrix,
        "sketch_origin_world_mm": origin,
        "sketch_world_axes": axes,
        "matrix_translation_units": "cm",
        "historical_measured_plane": {
            key: historical[key]
            for key in ("plane", "normal", "origin_mm", "x_direction", "y_direction")
        },
        "historical_curves": measured_curves,
        "geometry": [
            {
                **row,
                "record": record_site(data, primary[identity]),
                "historical_curve_index": line_indices.get(identity),
            }
            for identity, row in geometry.items()
        ],
        "constraints": [
            {**row, "record": record_site(data, primary[row["object_id"]])}
            for row in constraints
        ],
        "dimensions": dimensions,
        "historical_profile_area_mm2": historical["profile_areas_mm2"][0],
        "sketch_coverage": coverage,
    }


# the standalone capture uses local points while the shared capture already records world points
def historical_world_curves(historical):
    measured_curves = []
    for line in historical["entities"]:
        world_points = []
        for key in ("start_mm", "end_mm"):
            x, y, z = line[key]
            require(z == 0, "P01 historical local line is not within the sketch plane")
            world_points.append(
                [
                    origin + x * axis_x + y * axis_y
                    for origin, axis_x, axis_y in zip(
                        historical["origin_mm"],
                        historical["x_direction"],
                        historical["y_direction"],
                        strict=True,
                    )
                ]
            )
        measured_curves.append(
            {**line, "start_world_mm": world_points[0], "end_world_mm": world_points[1]}
        )
    return measured_curves


# only the original pinned discovery receipt controls which files and measurements enter the comparison
def report():
    git = GitSnapshot(ROOT)
    spec_bytes = git.blob(REVISION, SPECIFICATION)
    require(
        sha256(spec_bytes) == SPECIFICATION_SHA256,
        "paired specification digest differs",
    )
    spec = git.parse_document(spec_bytes, SPECIFICATION)
    (recipe,) = [row for row in spec["recipes"] if row["id"] == "P01"]
    require(recipe["split"] == "discovery", "unexpected P01 evidence split")
    capture = inspect_capture(
        git, REVISION, RECEIPT, recipe, "fusion", spec, SPECIFICATION_SHA256
    )
    require(
        capture["receipt"]["sha256"] == RECEIPT_SHA256,
        "P01 capture receipt digest differs",
    )
    measurement = capture["measurements"]
    measured = git.blob(REVISION, measurement["path"])
    require(sha256(measured) == measurement["sha256"], "P01 measurement digest differs")
    observations = historical_observations(
        capture, git.parse_document(measured, measurement["path"])
    )
    archives = []
    for source in capture["native_files"]:
        variant = source["variant"]
        phase, observed = observations[variant]
        (historical,) = observed["sketches"]
        streams, members = design_members(git.blob(REVISION, source["path"]))
        data = streams["BulkStream.dat"]
        records, index = design_records(data, streams["MetaStream.dat"])
        features = named_features(data, records)
        require(
            len(features) == 1
            and features[0]["kind"] == "Sketch"
            and features[0]["name"] == historical["name"] == "RectangleSketch",
            "unexpected P01 feature roster",
        )
        parameters, rejected = decode_stream(data, records)
        require(
            not rejected and not attach_parameters(data, records, features, parameters),
            "P01 parameters failed to bind",
        )
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                "design_members": members,
                **compare_sketch(data, records, index, features, historical, variant),
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
        "capture_qualification_blockers": capture["qualification_blockers"],
        "scope": "P01 saved reference plane, world frame and typed sketch operands; fresh live targets and editable acceptance remain open",
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
