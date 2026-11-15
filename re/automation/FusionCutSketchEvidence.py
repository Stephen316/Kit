import json
import math
from collections import Counter
from pathlib import PurePosixPath

from FusionCutExtentEvidence import REVISION, design_members, p04_capture, record_site
from PairedCaptureIntake import require, sha256

from decode_basics import attach_parameters, named_features
from decode_dimension_annotations import decode_dimension_annotations
from decode_dimension_controls import decode_dimension_controls
from decode_parameters import decode_stream
from decode_sketch import constraint_prefix, decode_sketches, numbers
from decode_sketch_coverage import decode_sketch_coverage
from fusion_metadata import design_records


# before and after save observations provide different strengths of archive comparison
def historical_observations(capture, measurements):
    observed = measurements["observations"]
    by_name = {
        PurePosixPath(row["path"]).name: row["variant"]
        for row in capture["native_files"]
    }
    observations = {
        "baseline-a": ("same_process_reopen", observed["fresh_reopen"]),
        "baseline-b": ("before_repeat_export", observed["unchanged_rebuild"]),
    }
    for row in [*observed["edits"], *observed["variants"]]:
        variant = by_name[row["export"]]
        require(variant not in observations, "duplicate historical Fusion observation")
        observations[variant] = ("same_process_reopen", row["reopened"])
    require(
        set(observations) == set(by_name.values()),
        "historical Fusion observations do not match the archive roster",
    )
    return observations


# the native collection order is useful evidence only within its historical observation
def match_lines(lines, observed):
    matched = {}
    for line in lines:
        # The independent measurement includes its own placement frame.
        points = [
            [
                origin + 10 * (point[0] * x + point[1] * y)
                for origin, x, y in zip(
                    observed["origin_world_mm"],
                    observed["x_direction"],
                    observed["y_direction"],
                    strict=True,
                )
            ]
            for point in (line["start_cm"], line["end_cm"])
        ]
        require(
            line["start_cm"][2] == line["end_cm"][2] == 0,
            "nonplanar saved P04 sketch line",
        )
        candidates = [
            curve
            for curve in observed["curves"]
            if curve["type"] == "SketchLine"
            and math.dist(curve["start_world_mm"], points[0]) <= 1e-6
            and math.dist(curve["end_world_mm"], points[1]) <= 1e-6
        ]
        require(
            len(candidates) == 1,
            "P04 saved line lacks a unique historical geometry match",
        )
        candidate = candidates[0]
        if "is_construction" in line:
            require(
                line["is_construction"] == candidate["construction"],
                "P04 construction state differs",
            )
        matched[line["object_id"]] = candidate["index"]
    require(
        len(set(matched.values())) == len(observed["curves"]) == len(lines),
        "P04 saved and historical line rosters differ",
    )
    return matched


# contradictory cached copies must remain visible alongside verified operand identities
def cache_witness(data, record, dimension, caches, refusals):
    identity = dimension["object_id"]
    if identity in caches:
        return {"status": "validated", **caches[identity]}
    payload = data[record.body : record.end]
    _, _, offset = constraint_prefix(payload)
    return {
        "status": "unresolved",
        "reason": refusals[identity]["reason"],
        "geometry_cache_offset": record.body + offset,
        "stored_second_anchor_cm": numbers(payload, offset + 72, 3),
        "stored_repeated_anchor_cm": numbers(payload, offset + 105, 3),
        "cached_measurement_cm": numbers(payload, offset + 97, 1)[0],
    }


# both the saved graph and the historical native inventory are needed for comparison
def inspect_sketches(content, observed):
    streams, members = design_members(content)
    data = streams["BulkStream.dat"]
    records, index = design_records(data, streams["MetaStream.dat"])
    primary = {record.object_id: record for record in records if record.is_primary}
    require(
        len(primary) == sum(record.is_primary for record in records),
        "ambiguous P04 primary record",
    )
    features = named_features(data, records)
    parameters, rejected = decode_stream(data, records)
    require(
        not rejected and not attach_parameters(data, records, features, parameters),
        "P04 parameters failed to bind",
    )
    summary = decode_sketches(
        data, records, features, allow_reversed_point_dimensions=True
    )
    coverage = decode_sketch_coverage(data, records, features, index, summary)
    require(
        coverage["status"] == "Observed class-family accounting"
        and not coverage["unhandled"],
        "P04 sketch record coverage has unresolved candidates",
    )
    controls = decode_dimension_controls(data, records, features)
    require(
        not controls["unresolved"], "P04 dimension control parser refused a binding"
    )
    annotations = decode_dimension_annotations(data, records, features, controls)
    caches = {row["object_id"]: row for row in annotations["decoded"]}
    refusals = {row["object_id"]: row for row in annotations["unresolved"]}
    controls_by_id = {row["object_id"]: row for row in controls["decoded"]}
    saved_sketches = [feature for feature in features if feature["kind"] == "Sketch"]
    require(
        {sketch["name"] for sketch in saved_sketches}
        == {"RectangleSketch", "CutSketch"}
        and len(saved_sketches) == len(observed["sketches"]) == 2,
        "unexpected P04 sketch roster",
    )
    observed_sketches = {sketch["name"]: sketch for sketch in observed["sketches"]}
    parameter_values = {
        param["name"]: param["value_internal"] for param in observed["parameters"]
    }
    sketches = []
    for feature in saved_sketches:
        history = observed_sketches[feature["name"]]
        lines = [item for item in feature["geometry"] if item["kind"] == "Line"]
        points = [item for item in feature["geometry"] if item["kind"] == "Point"]
        require(
            len(points) == history["point_count"]
            and len(points) + len(lines) == len(feature["geometry"]),
            "P04 geometry roster differs",
        )
        line_indices = match_lines(lines, history)
        constraints = feature["constraints"]
        require(
            Counter(row["kind"] + "Constraint" for row in constraints)
            == Counter(row["type"] for row in history["constraints"]),
            "P04 constraint inventory differs",
        )
        dimensions = feature["dimensions"]
        dimensions_by_name = {row["parameter"]: row for row in history["dimensions"]}
        require(
            len(dimensions) == len(history["dimensions"]) == len(dimensions_by_name)
            and {row["parameter_name"] for row in dimensions}
            == set(dimensions_by_name),
            "P04 dimension roster differs",
        )
        dimension_rows = []
        for dimension in dimensions:
            identity = dimension["object_id"]
            name = dimension["parameter_name"]
            prior = dimensions_by_name[name]
            control = controls_by_id[identity]
            require(
                prior["type"] == "SketchLinearDimension"
                and dimension["kind"] == "Linear"
                and prior["driving"] is control["is_driving"]
                and prior["expression"] == control["stored_value_expression_text"]
                and math.isclose(
                    parameter_values[name], dimension["raw_value"], abs_tol=1e-9
                ),
                f"P04 bound dimension disagrees with historical measurement: {name}",
            )
            dimension_rows.append(
                {
                    **dimension,
                    "dependency_entity_ids": dimension.get(
                        "dependency_entity_ids", dimension["entity_ids"]
                    ),
                    "record": record_site(data, primary[identity]),
                    "binding_record": record_site(
                        data, primary[dimension["binding_object_id"]]
                    ),
                    "historical_dimension": prior,
                    "measurement_cache": cache_witness(
                        data, primary[identity], dimension, caches, refusals
                    ),
                }
            )
        sketches.append(
            {
                "name": feature["name"],
                "feature_record": record_site(data, primary[feature["object_id"]]),
                "sketch_record": record_site(
                    data, primary[feature["sketch_object_id"]]
                ),
                "geometry": [
                    {
                        **item,
                        "record": record_site(data, primary[item["object_id"]]),
                        "historical_curve_index": line_indices.get(item["object_id"]),
                    }
                    for item in feature["geometry"]
                ],
                "constraints": [
                    {**row, "record": record_site(data, primary[row["object_id"]])}
                    for row in constraints
                ],
                "dimensions": dimension_rows,
            }
        )
    return {
        "design_members": members,
        "sketch_coverage": coverage,
        "sketches": sketches,
    }


# immutable capture bytes keep the saved evidence independent of later native verification
def report():
    git, capture = p04_capture()
    measurement_path = capture["measurements"]["path"]
    data = git.blob(REVISION, measurement_path)
    require(
        sha256(data) == capture["measurements"]["sha256"],
        "P04 measurement digest differs",
    )
    observations = historical_observations(
        capture, git.parse_document(data, measurement_path)
    )
    archives = []
    for row in capture["native_files"]:
        phase, observation = observations[row["variant"]]
        archives.append(
            {
                "source": row,
                "historical_observation": {
                    "phase": phase,
                    "label": observation["label"],
                },
                **inspect_sketches(git.blob(REVISION, row["path"]), observation),
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
        "scope": "Saved participant records and historical native inventory; exact live target getters and edit acceptance pending",
        "archives": archives,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
