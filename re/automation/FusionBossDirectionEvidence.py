import json
import math
from pathlib import PurePosixPath

from FusionCutExtentEvidence import (
    EXTRUDE_CLASS,
    REVISION,
    ROOT,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    along_binding,
    design_members,
    record_site,
)
from FusionCutSketchEvidence import historical_observations
from PairedCaptureIntake import GitSnapshot, inspect_capture, require, sha256

from decode_basics import attach_parameters, named_features
from decode_extrude import decode_extrude
from decode_parameters import decode_stream
from decode_placement import cross
from decode_sketch import same
from fusion_metadata import design_records

# the receipt pins the authored direction controls before any archive decoding
RECEIPT = "re/automation/PairedCaptures/P03/fusion-8d53584027ff/receipt.json"

# a fixed receipt digest detects changed provenance even when variant names match
RECEIPT_SHA256 = "f42a7e81b9ae108ba69d440ff411a8828dbc9ee0bbd54d6242c22370cf6560b8"
SOLIDWORKS_RECEIPT = (
    "re/automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json"
)
SOLIDWORKS_RECEIPT_SHA256 = (
    "f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94"
)


# the separate axis and sign controls distinguish which native field moves the solid
def inspect_boss(content, variant, recipe, observed):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, _ = design_records(data, streams["MetaStream.dat"])
    features = named_features(data, records)
    parameters, rejected = decode_stream(data, records)
    require(
        not rejected and not attach_parameters(data, records, features, parameters),
        "P03 feature parameters did not bind",
    )
    (feature,) = [row for row in features if row["kind"] == "Extrude"]
    (record,) = [row for row in records if row.start == feature["record_offset"]]
    require(
        record.is_primary
        and record.class_guid == EXTRUDE_CLASS
        and feature["name"] == "BlindBoss",
        "P03 does not contain the expected primary boss feature",
    )
    controls, unresolved = decode_extrude(
        data[record.body : record.end], feature, allow_surface=True
    )
    extent = controls["extent"]
    side = extent["side_one"]
    require(
        not unresolved
        and controls["operation"]["kind"] == "NewBody"
        and controls["is_solid"]
        and extent["mode"] == "OneSided"
        and controls["stored_second_extent_enabled"] == 0
        and controls["start"]["kind"] == "ProfilePlane"
        and side["condition"] == "Distance",
        "P03 boss is outside the one-sided blind solid control family",
    )

    expected_mm = dict(recipe["driving_parameters"])
    for edit in recipe["independent_edits"]:
        if variant == f"edit-{edit['parameter']}-{edit['value']}":
            expected_mm[edit["parameter"]] = edit["value"]
    if variant == "direction-negative":
        expected_mm["depth_mm"] *= -1
    stored_vector = extent["stored_direction_vector"]
    expected_vector = (
        [1, 0, 0] if variant == "plane-yz" else recipe["operation"]["direction_world"]
    )
    (along,) = [
        along_binding(data, parameter)
        for parameter in feature["parameters"]
        if parameter["role"] == "AlongDistance"
    ]
    signed_cm = along["raw_value_cm"]
    require(
        same(stored_vector, expected_vector)
        and along["parameter_name"] == "depth_mm"
        and math.isclose(signed_cm * 10, expected_mm["depth_mm"], abs_tol=1e-9)
        and signed_cm == side["distance_cm"],
        "P03 saved direction or signed AlongDistance differs",
    )

    observed_parameters = {row["name"]: row for row in observed["parameters"]}
    require(
        all(
            math.isclose(
                observed_parameters[name]["value_internal"] * 10, value, abs_tol=1e-9
            )
            for name, value in expected_mm.items()
        )
        and observed_parameters["depth_mm"]["expression"]
        in along["expression_candidates"],
        "P03 historical API parameters do not match the bound values",
    )
    (sketch,) = observed["sketches"]
    (body,) = observed["bodies"]
    require(
        sketch["name"] == "RectangleSketch"
        and body["solid"]
        and same(cross(sketch["x_direction"], sketch["y_direction"]), stored_vector),
        "P03 stored vector differs from the historical sketch normal",
    )
    (axis,) = [
        index for index, component in enumerate(expected_vector) if component == 1
    ]
    start_mm = sketch["origin_world_mm"][axis]
    bounds = [point[axis] for point in body["bounding_box_mm"]]
    require(
        same(bounds, sorted((start_mm, start_mm + 10 * signed_cm))),
        "P03 historical solid bounds contradict the signed extent on its world axis",
    )
    return {
        "design_members": members,
        "boss_record": record_site(data, record),
        "controls": controls,
        "signed_along_distance": along,
        "historical_depth_parameter": observed_parameters["depth_mm"],
        "historical_sketch_frame": {
            key: sketch[key]
            for key in ("origin_world_mm", "x_direction", "y_direction")
        },
        "measured_bounding_box_mm": body["bounding_box_mm"],
        "extent_axis_index": axis,
        "measured_world_axis_bounds_mm": bounds,
        "measured_volume_mm3": body["volume_mm3"],
    }


# a rectangular prism's mass center lies halfway from its sketch section to the end
def compare_solidworks_direction(left, right, measured, tolerances):
    (boss,) = [
        feature for feature in left["feature_tree"] if feature["name"] == "BlindBoss"
    ]
    (sketch,) = left["sketches"]
    operation = boss["operation"]
    require(
        operation["end_condition"] == 0
        and operation["both_directions"] is False
        and type(operation["reverse_direction"]) is bool
        and boss["suppressed"] is False
        and sketch["name"] == "RectangleSketch"
        and left["body_count"] == right["body_count"] == 1,
        "SOLIDWORKS native P03 blind boss is outside the observed family",
    )
    sign = -1 if operation["reverse_direction"] else 1
    solidworks_depth_mm = sign * 1000 * operation["depth_m"]
    fusion_depth_mm = 10 * measured["signed_along_distance"]["raw_value_cm"]
    axis = measured["controls"]["extent"]["stored_direction_vector"]
    displacement_mm = [
        2 * (end - start)
        for end, start in zip(
            left["center_of_mass_mm"], sketch["section_center_world_mm"], strict=True
        )
    ]
    fusion_displacement = [component * fusion_depth_mm for component in axis]
    center_error = math.dist(left["center_of_mass_mm"], right["center_of_mass_mm"])
    volume_error = abs(left["volume_mm3"] - right["volume_mm3"])
    tolerance = tolerances["length_mm_absolute"]
    require(
        abs(solidworks_depth_mm - fusion_depth_mm) <= tolerance
        and math.dist(displacement_mm, fusion_displacement) <= tolerance
        and center_error <= tolerance
        and volume_error
        <= max(
            tolerances["volume_mm3_absolute"],
            tolerances["volume_relative"]
            * max(left["volume_mm3"], right["volume_mm3"]),
        ),
        "P03 historical physical measurements disagree on the saved boss direction",
    )
    return {
        "solidworks_operation": operation,
        "solidworks_signed_depth_mm": solidworks_depth_mm,
        "solidworks_displacement_from_section_and_mass_center_mm": displacement_mm,
        "fusion_displacement_from_saved_axis_and_depth_mm": fusion_displacement,
        "center_of_mass_difference_mm": center_error,
        "volume_difference_mm3": volume_error,
    }


# historical observations and saved bytes come from the same verified P03 capture roster
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
    solidworks = inspect_capture(
        git,
        REVISION,
        SOLIDWORKS_RECEIPT,
        recipe,
        "solidworks",
        specification,
        SPECIFICATION_SHA256,
    )
    require(
        solidworks["receipt"]["sha256"] == SOLIDWORKS_RECEIPT_SHA256
        and solidworks["canonical_recipe_sha256"] == capture["canonical_recipe_sha256"],
        "P03 SOLIDWORKS capture receipt or recipe digest differs",
    )
    solidworks_readback = git.document(REVISION, solidworks["measurements"]["path"])
    require(
        solidworks_readback["authoring_process_id"]
        != solidworks_readback["reopen_process_id"]
        and not solidworks_readback["errors"],
        "P03 SOLIDWORKS independent reopen was not measured",
    )
    peers = {row["variant"]: row for row in solidworks["native_files"]}
    reopened = solidworks_readback["observations"]["reopened_files"]
    measurement = capture["measurements"]
    data = git.blob(REVISION, measurement["path"])
    require(sha256(data) == measurement["sha256"], "P03 measurement digest differs")
    observations = historical_observations(
        capture, git.parse_document(data, measurement["path"])
    )
    variants = {row["variant"] for row in capture["native_files"]}
    require(
        variants
        == {
            "baseline-a",
            "baseline-b",
            "edit-width_mm-41",
            "edit-height_mm-23",
            "edit-depth_mm-12",
            "units-inch",
            "plane-yz",
            "direction-negative",
        },
        "unexpected P03 saved variant roster",
    )
    require(
        set(peers) == variants and len(peers) == len(solidworks["native_files"]),
        "P03 paired archive rosters differ",
    )
    archives = []
    for source in capture["native_files"]:
        variant = source["variant"]
        phase, observed = observations[variant]
        measured = inspect_boss(
            git.blob(REVISION, source["path"]), variant, recipe, observed
        )
        peer = peers[variant]
        readback = reopened[PurePosixPath(peer["path"]).name]
        require(
            readback["open_status"] == {"errors": 0, "warnings": 0},
            "P03 SOLIDWORKS reopen warned or failed",
        )
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                "solidworks_source": peer,
                "paired_direction": compare_solidworks_direction(
                    readback, observed, measured, specification["comparison_tolerances"]
                ),
                **measured,
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
        "solidworks_receipt": solidworks["receipt"],
        "solidworks_measurements": solidworks["measurements"],
        "capture_qualification_blockers": capture["qualification_blockers"],
        "archives": archives,
        "scope": "Saved P03 blind-boss direction and historical API bounding box; fresh native qualification remains open",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
