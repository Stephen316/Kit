import json

from FusionBossDirectionEvidence import RECEIPT, RECEIPT_SHA256, inspect_boss
from FusionCutExtentEvidence import (
    EXTRUDE_CLASS,
    REVISION,
    ROOT,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    counted_references,
    design_members,
    record_site,
)
from FusionCutSketchEvidence import historical_observations
from FusionRectangleSketchEvidence import compare_sketch
from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256

from decode_basics import attach_parameters, named_features, sketch_references
from decode_body_selections import PROXY
from decode_parameters import decode_stream
from decode_placement import cross
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, decode_profiles
from decode_selection import native_proxy_references
from decode_sketch import reference
from fusion_metadata import design_records


# the shared capture records world lines and document parameters in separate api inventories
def normalized_rectangle(observed):
    (sketch,) = observed["sketches"]
    require(
        sketch["name"] == "RectangleSketch"
        and sketch["support"] == "ConstructionPlane"
        and len(sketch["curves"]) == 4
        and all(
            row["type"] == "SketchLine" and not row["reference"]
            for row in sketch["curves"]
        ),
        "unexpected P03 historical rectangle inventory",
    )
    values = {row["name"]: row["value_internal"] for row in observed["parameters"]}
    return {
        "name": sketch["name"],
        "plane": sketch["support_name"],
        "origin_mm": sketch["origin_world_mm"],
        "x_direction": sketch["x_direction"],
        "y_direction": sketch["y_direction"],
        "normal": cross(sketch["x_direction"], sketch["y_direction"]),
        "point_count": sketch["point_count"],
        "other_curve_count": 0,
        "constraints": sketch["constraints"],
        "fully_constrained": sketch["fully_constrained"],
        "profile_areas_mm2": sketch["profile_areas_mm2"],
        "dimensions": [
            {**row, "value_mm": 10 * values[row["parameter"]]}
            for row in sketch["dimensions"]
        ],
    }, sketch["curves"]


# the boss must select the same closed four line membership that the sketch proof established
def selected_profile(data, records, features, sketch, boss):
    primary = {record.object_id: record for record in records if record.is_primary}
    require(
        len(primary) == sum(record.is_primary for record in records),
        "ambiguous P03 primary entity",
    )
    feature = primary[boss["object_id"]]
    payload = data[feature.body : feature.end]
    require(
        feature.class_guid == EXTRUDE_CLASS
        and feature.start == boss["record_offset"]
        and len(payload) == 426,
        "unexpected P03 boss profile layout",
    )
    proxy = primary[reference(payload, 132)]
    proxy_payload = data[proxy.body : proxy.end]
    require(
        proxy.class_guid == PROXY
        and len(proxy_payload) == 105
        and reference(proxy_payload, 94) == boss["object_id"],
        "P03 boss profile proxy ownership differs",
    )
    descriptor_ids, attributes = native_proxy_references(data, proxy)
    require(
        len(descriptor_ids) == 1 and not attributes,
        "unexpected P03 profile descriptor count",
    )
    descriptor = primary[descriptor_ids[0]]
    repeated_dependencies = counted_references(payload, 249, 5)
    require(
        descriptor.class_guid == PROFILE_DESCRIPTOR_GUID
        and reference(data, descriptor.end - 11) == boss["object_id"]
        and repeated_dependencies[:2] == [proxy.object_id, descriptor.object_id],
        "P03 owner and repeated profile dependency references disagree",
    )

    sketch_references(data, records, features)
    (reference_row,) = boss["sketch_reference_candidates"]
    require(
        reference_row["reference_record_offset"] == descriptor.start
        and reference_row["sketch_object_id"] == sketch["sketch_object_id"]
        and reference_row["feature_object_id"] == sketch["object_id"],
        "P03 profile descriptor names another sketch",
    )
    profiles = decode_profiles(data, records, features)
    require(
        len(profiles["decoded"]) == 1 and not profiles["unresolved"],
        "P03 profile loop unresolved",
    )
    (selection,) = boss["profile_selection"]
    definition = primary[selection["loop_definition_object_id"]]
    require(
        definition.class_guid == PROFILE_LOOP_GUID
        and selection["descriptor_object_id"] == descriptor.object_id,
        "P03 profile definition differs from the selected descriptor",
    )
    (loop,) = selection["loops"]
    curves = loop["curve_references"]
    lines = {
        row["object_id"]
        for row in sketch["geometry"]
        if row["kind"] == "Line" and not row["is_construction"]
    }
    require(
        loop["is_outer"]
        and len(curves) == len(lines) == 4
        and all(row["entity_kind"] == "Line" for row in curves)
        and {row["entity_id"] for row in curves} == lines,
        "P03 profile does not select the entire rectangle perimeter",
    )
    return {
        "boss": record_site(data, feature),
        "profile_proxy": record_site(data, proxy),
        "profile_descriptor": record_site(data, descriptor),
        "profile_loop_definition": record_site(data, definition),
        "selection": selection,
        "owner_repeated_dependency_object_ids": repeated_dependencies,
    }


# exact p03 variants share the native rectangle proof without conflating their measured field layouts
def inspect_profile(content, variant, recipe, observed):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, index = design_records(data, streams["MetaStream.dat"])
    features = named_features(data, records)
    sketch, boss = features
    require(
        sketch["kind"] == "Sketch"
        and sketch["name"] == "RectangleSketch"
        and boss["kind"] == "Extrude"
        and boss["name"] == "BlindBoss"
        and [(row["name"], row["type"]) for row in observed["feature_tree"]]
        == [("RectangleSketch", "Sketch"), ("BlindBoss", "ExtrudeFeature")],
        "unexpected P03 saved or historical feature roster",
    )
    parameters, rejected = decode_stream(data, records)
    require(
        not rejected and not attach_parameters(data, records, features, parameters),
        "P03 native parameters failed to bind",
    )
    historical, world_curves = normalized_rectangle(observed)
    rectangle = compare_sketch(
        data,
        records,
        index,
        [sketch],
        historical,
        variant,
        measured_world_curves=world_curves,
    )
    rectangle["historical_measured_plane"][
        "normal_source"
    ] = "Cross product of measured sketch axes; support plane name is a direct getter"
    rectangle["historical_dimension_value_source"] = (
        "Original Fusion document parameter values converted from centimeters to millimeters"
    )
    return {
        "design_members": members,
        "rectangle": rectangle,
        "boss_profile": selected_profile(data, records, features, sketch, boss),
        "boss_controls": inspect_boss(content, variant, recipe, observed),
    }


# immutable p03 source and measurements keep the new join independent of native reruns
def report():
    git = GitSnapshot(ROOT)
    spec_bytes = git.blob(REVISION, SPECIFICATION)
    require(
        sha256(spec_bytes) == SPECIFICATION_SHA256,
        "paired specification digest differs",
    )
    specification = git.parse_document(spec_bytes, SPECIFICATION)
    (recipe,) = [row for row in specification["recipes"] if row["id"] == "P03"]
    require(recipe["split"] == "discovery", "unexpected P03 evidence split")
    capture = inspect_capture(
        git, REVISION, RECEIPT, recipe, "fusion", specification, SPECIFICATION_SHA256
    )
    require(
        capture["receipt"]["sha256"] == RECEIPT_SHA256,
        "P03 capture receipt digest differs",
    )
    measurement = capture["measurements"]
    data = git.blob(REVISION, measurement["path"])
    require(sha256(data) == measurement["sha256"], "P03 measurement digest differs")
    historical = historical_observations(
        capture, git.parse_document(data, measurement["path"])
    )
    archives = []
    for source in capture["native_files"]:
        variant = source["variant"]
        phase, observed = historical[variant]
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                **inspect_profile(
                    git.blob(REVISION, source["path"]), variant, recipe, observed
                ),
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
        "scope": "Saved P03 rectangle support, operands and selected boss profile; fresh native targets and editable acceptance remain open",
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
