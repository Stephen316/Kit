# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import math
from pathlib import Path

from FusionCircularLoopEvidence import saved_circle_loop
from PairedCaptureIntake import GitSnapshot, require, sha256
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import (
    KDiaDimension,
    KRadiusDimension,
)
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.base.ReadOptions import ReadOptions
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Enums.EnumValues import ParameterRole, ValueKind

ROOT = Path(__file__).resolve().parents[2]
REVISION = "38079a7c1da24a3685af0e4c74854a8297006c80"
FOLDER = "re/Fusion/Study/dimcontrols-2a0d0bdbc8a6/"
MEASUREMENTS = "dabc64135de96c4c54a7cdb51a8c2829b54d2a8388ca17cc41e57a18692726c3"
CONTROLS = {
    "diameter_driving.f3d": (
        "diameter",
        True,
        85309,
        "d9f6919c150c93fbca1b2ad78540ff985757da7dbaacdbe25c9f8c8fe22e583b",
    ),
    "diameter_reference.f3d": (
        "diameter",
        False,
        85393,
        "2bb5a639b34bda71a1ef423943c75606512a22ff358495d6acea49c48cc02406",
    ),
    "radius_driving.f3d": (
        "radius",
        True,
        85397,
        "345668081d261cab25b0b3c21ab1edf3ac1bcbfe097738ab8d9add5f16c75205",
    ),
    "radius_reference.f3d": (
        "radius",
        False,
        85355,
        "236bc3431b873f7b8e58bec1cd98640dabd66db436ebf2057da2c9ba6b976e18",
    ),
}
DIMENSIONS = {
    "diameter": (
        "Na::FusionSketchDiameterDim",
        KDiaDimension,
        "adsk::fusion::SketchDiameterDimension",
    ),
    "radius": (
        "Na::FusionSketchRadialDim",
        KRadiusDimension,
        "adsk::fusion::SketchRadialDimension",
    ),
}
LENGTH_TOLERANCE_MM = 1e-6


def close_mm(actual, measured):
    return math.isclose(actual, measured, rel_tol=0.0, abs_tol=LENGTH_TOLERANCE_MM)


def strict_observation(reader, payload, model, sample, kind, driving):
    name, expected, _ = DIMENSIONS[kind]
    record = BuildGraph(model).OneClass(name.removeprefix("Na::"))
    document = reader.Read(payload, ReadOptions(strict=True))
    (sketch,) = document.sketches
    (parameter,) = document.parameters
    (feature,) = document.feature_timeline
    (relation,) = sketch.constraints
    (circle,) = (
        entity for entity in sketch.entities if entity.kind == GeometryKind.KCircle
    )
    measured = sample["dimension"]
    require(
        record.Groups[0].ClassGuid.upper() == expected
        and not document.bodies
        and not document.diagnostics
        and not document.metadata
        and sketch.name == sample["sketch_name"]
        and layout_matches(sketch, feature, circle, relation, parameter, record)
        and relation.kind == kind
        and relation.driving is measured["is_driving"] is driving
        and parameter.role
        is (ParameterRole.KDriving if driving else ParameterRole.KReference)
        and parameter.name == measured["parameter_name"]
        and parameter.expression is not None
        and parameter.expression.source == measured["parameter_expression"]
        and parameter.value.kind is ValueKind.KLength
        and parameter.value.unit == "mm"
        and close_mm(parameter.value.value, measured["parameter_value"] * 10.0),
        "Packaged strict circle output differs from its native observation",
    )
    return {
        "status": "read-only",
        "primary": {
            "segment": record.SegmentId,
            "object_id": record.ObjectId,
            "guid": expected,
            "class": name,
        },
        "circle": compared_geometry(circle, sample["geometry"][0]),
        "closed_profile_entity_ids": sketch.closed_profile_entity_ids,
        "relation_id": relation.id,
        "parameter_id": parameter.id,
        "owner_id": feature.id,
        "driving": driving,
        "parameter_role": parameter.role.value,
    }


def layout_matches(sketch, feature, circle, relation, parameter, record):
    return (
        sketch.closed_profile_entity_ids == ((circle.id,),)
        and relation.id == record.Identity
        and tuple((ref.entity_id, ref.point) for ref in relation.references)
        == ((circle.id, ""),)
        and relation.parameter_id == parameter.id
        and feature.sketch_id == sketch.id
        and parameter.owner_id == feature.id
        and sketch.parameter_ids == feature.parameter_ids == (parameter.id,)
    )


def compared_geometry(circle, observed):
    geometry = circle.geometry
    center = [geometry.center.x, geometry.center.y, 0.0]
    native_center = [value * 10.0 for value in observed["center_cm"]]
    native_radius = observed["radius_cm"] * 10.0
    require(
        observed["kind"] == "SketchCircle"
        and len(native_center) == 3
        and all(
            close_mm(value, truth)
            for value, truth in zip(center, native_center, strict=True)
        )
        and close_mm(geometry.radius, native_radius),
        "Neutral circle geometry differs from the native observation",
    )
    return {
        "center_mm": center,
        "radius_mm": geometry.radius,
        "measured_center_mm": native_center,
        "measured_radius_mm": native_radius,
    }


def compared_binding(
    dimension, parameter, feature, circle, record, measured, kind, driving
):
    require(
        dimension.id == f"fusion-sketch-dimension-{record}"
        and len(dimension.references) == 1
        and dimension.references[0].entity_id == circle.id
        and dimension.references[0].point == ""
        and dimension.parameter_id == parameter.id
        and parameter.owner_id == feature.id
        and feature.parameter_ids == (parameter.id,),
        "Circular dimension, sketch owner, circle and parameter do not form one binding",
    )
    binding = parameter.attributes.get("fusion.binding_id")
    require(
        type(binding) is int
        and dimension.attributes.get("fusion.binding_id") == binding,
        "Circular dimension and parameter record bindings disagree",
    )
    require(
        dimension.kind == kind
        and dimension.driving is driving
        and measured["is_driving"] is driving
        and measured["object_type"] == DIMENSIONS[kind][2]
        and parameter.name == measured["parameter_name"]
        and parameter.expression is not None
        and parameter.expression.source == measured["parameter_expression"]
        and parameter.attributes.get("fusion.native_role") == measured["parameter_role"]
        and parameter.attributes.get("fusion.display_unit")
        == measured["parameter_unit"],
        "Neutral dimension type, mode, expression or display units differ from native",
    )
    expected_role = ParameterRole.KDriving if driving else ParameterRole.KReference
    require(
        parameter.role is expected_role,
        "Neutral circle parameter role differs from native mode",
    )
    native_value = measured["parameter_value"] * 10.0
    require(
        parameter.value.kind == ValueKind.KLength
        and parameter.value.unit == "cm"
        and close_mm(parameter.value.value * 10.0, native_value)
        and close_mm(measured["value"] * 10.0, native_value),
        "Circular dimension parameter value differs from native",
    )
    return {
        "relation_id": dimension.id,
        "kind": dimension.kind,
        "driving": dimension.driving,
        "native_type": measured["object_type"],
        "native_driving": measured["is_driving"],
        "circle_id": circle.id,
        "parameter_id": parameter.id,
        "feature_id": feature.id,
        "binding_id": binding,
        "parameter_name": parameter.name,
        "parameter_role": parameter.role.value,
        "native_parameter_role": measured["parameter_role"],
        "expression": parameter.expression.source,
        "value_mm": parameter.value.value * 10.0,
        "measured_value_mm": native_value,
        "display_unit": measured["parameter_unit"],
    }


def partial_observation(reader, payload, model, sample, kind, driving, native_record):
    document = reader.Read(payload, ReadOptions(strict=False))
    require(
        len(document.sketches)
        == len(document.parameters)
        == len(document.feature_timeline)
        == 1
        and not document.bodies,
        "Expected one sketch, one parameter and no bodies",
    )
    sketch, parameter, feature = (
        document.sketches[0],
        document.parameters[0],
        document.feature_timeline[0],
    )
    circles = [row for row in sketch.entities if row.kind == GeometryKind.KCircle]
    require(
        len(circles) == len(sketch.constraints) == len(sample["geometry"]) == 1
        and sketch.name == sample["sketch_name"]
        and feature.sketch_id == sketch.id,
        "Circular source does not resolve to its sole neutral sketch and dimension",
    )
    return {
        "status": "partial",
        "circle": compared_geometry(circles[0], sample["geometry"][0]),
        "dimension": compared_binding(
            sketch.constraints[0],
            parameter,
            feature,
            circles[0],
            native_record,
            sample["dimension"],
            kind,
            driving,
        ),
        "saved_sheet_loop": saved_circle_loop(
            payload, model, sketch, feature, circles[0], native_record
        ),
        "closed_profile_entity_ids": sketch.closed_profile_entity_ids,
        "support_plane_id": sketch.support_plane_id,
        "diagnostic_codes": [item.code for item in document.diagnostics],
    }


def report():
    snapshot = GitSnapshot(ROOT)
    path = FOLDER + "ground_truth.json"
    raw = snapshot.blob(REVISION, path)
    require(sha256(raw) == MEASUREMENTS, "Historical Fusion observation digest changed")
    observed = snapshot.parse_document(raw, path)
    require(
        observed["fusion_version"] == "2705.1.30" and not observed["errors"],
        "Historical Fusion build or capture state differs",
    )
    measurements = {}
    for item in observed["samples"]:
        name = item["file"]
        if name in CONTROLS:
            require(name not in measurements, "Duplicate historical circle control")
            measurements[name] = item
    require(
        set(measurements) == set(CONTROLS), "Historical circle control roster changed"
    )
    reader = FusionReader()
    cases = {}
    for filename, (kind, driving, size, digest) in CONTROLS.items():
        sample = measurements[filename]
        payload = snapshot.blob(REVISION, FOLDER + filename)
        require(
            len(payload) == size
            and sha256(payload) == digest
            and sample["kind"] == kind,
            f"Historical circle control differs: {filename}",
        )
        model = ReadDocument(payload)
        strict = strict_observation(reader, payload, model, sample, kind, driving)
        cases[filename] = {
            "archive_sha256": digest,
            "archive_bytes": size,
            "strict": strict,
            "partial": partial_observation(
                reader,
                payload,
                model,
                sample,
                kind,
                driving,
                strict["primary"]["object_id"],
            ),
        }
    return {
        "schema": 1,
        "scope": "historical circular dimension discovery",
        "source_revision": REVISION,
        "fusion_version": observed["fusion_version"],
        "measurement_sha256": MEASUREMENTS,
        "measurement_binding": "historical API observations joined by filename in the Git-pinned capture tree; capture-time digests unavailable",
        "qualification": "strict read-only circular discovery; writer qualification outside scope",
        "length_tolerance_mm": LENGTH_TOLERANCE_MM,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True))
