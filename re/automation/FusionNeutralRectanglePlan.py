# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from pathlib import Path

from PairedCaptureIntake import GitSnapshot, require, sha256
from PairedPerimeters import edge_gap, match_perimeters
from RectanglePairBoss import solidworks_boss
from RectanglePairEvidence import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    capture,
    load_public,
    rectangle_side,
)
from RectanglePairSketch import bound_point, parameter_mm, unique, world, xyz
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Writer import FusionWriter
from interchange import NativeFeatureDefinition
from interchange.geometry.Models.GeometryCurves import LineGeometry

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = {
    "P01": ("baseline-a", "edit-width_mm-41", "edit-height_mm-23"),
    "P03": ("baseline-a", "edit-width_mm-41", "edit-height_mm-23", "edit-depth_mm-12"),
}
AXES = {"width_mm": ("distance_x", 0), "height_mm": ("distance_y", 1)}


def trace(parameter):
    expression = parameter.expression
    return {
        "id": parameter.id,
        "name": parameter.name,
        "owner_id": parameter.owner_id,
        "role": str(parameter.role),
        "value": parameter.value.value,
        "unit": parameter.value.unit,
        "expression": expression.source if expression is not None else None,
        "dependencies": expression.parameter_ids if expression is not None else (),
    }


def operand_ids(rule):
    return [(reference.entity_id, reference.point) for reference in rule.references]


def provenance(origin):
    require(origin is not None, "Expected the original native binding provenance")
    return [
        [span.stream, span.record_kind, span.offset, span.length]
        for span in origin.spans
    ]


def axis_bindings(source, measured, target, links, tolerance):
    (target_sketch,) = target.sketches
    (target_frame,) = target.support_planes
    target_entities = {row.id: row for row in target_sketch.entities}
    source_parameters = {row.id: row for row in source.parameters}
    target_parameters = {row.id: row for row in target.parameters}
    source_sketch = measured["sketch"]
    rows = {}
    for name, (target_kind, axis) in AXES.items():
        original = measured["dimensions"][name]
        source_rule = unique(
            (
                row
                for row in source_sketch.constraints
                if row.id == original["relation_id"]
            ),
            "original size relation",
        )
        parameter = source_parameters[original["parameter_id"]]
        source_owner = unique(
            (row for row in source.feature_timeline if row.id == parameter.owner_id),
            "source sketch parameter owner",
        )
        target_rule = unique(
            (row for row in target_sketch.constraints if row.kind == target_kind),
            "constructor size relation",
        )
        model_parameter = target_parameters[target_rule.parameter_id]
        (driver_id,) = model_parameter.expression.parameter_ids
        driver = target_parameters[driver_id]
        points = tuple(
            world(target_frame.transform, bound_point(target_entities, operand))
            for operand in target_rule.references
        )
        first, second = original["operands_world_mm"]
        require(
            source_owner.sketch_id == source_sketch.id
            and parameter.id in source_owner.parameter_ids
            and parameter.role == "driving"
            and abs(first[axis] - second[axis]) > tolerance
            and all(
                abs(a - b) <= tolerance
                for index, (a, b) in enumerate(zip(first, second, strict=True))
                if index != axis
            )
            and target_rule.driving
            and model_parameter.owner_id == target_sketch.id
            and driver.name == parameter.name
            and not driver.owner_id
            and abs(parameter_mm(driver) - original["value_mm"]) <= tolerance
            and abs(parameter_mm(model_parameter) - original["value_mm"]) <= tolerance
            and edge_gap(points, (first, second)) <= tolerance,
            "Source and constructor size binding do not describe the verified side and value",
        )
        rows[name] = {
            "source": {
                **original,
                "ordered_operands": operand_ids(source_rule),
                "parameter": trace(parameter),
                "relation_spans": provenance(source_rule.provenance),
                "parameter_spans": provenance(parameter.provenance),
            },
            "constructor": {
                "relation_id": target_rule.id,
                "kind": target_rule.kind,
                "ordered_operands": operand_ids(target_rule),
                "operands_world_mm": points,
                "side_id": links[original["perimeter_id"]],
                "model_parameter": trace(model_parameter),
                "user_parameter": trace(driver),
            },
        }
    return rows


def constructor(source, measured, boss):
    dimensions = measured["dimensions"]
    source_sketch = measured["sketch"]
    depth = next(
        (
            row
            for row in source.parameters
            if boss and row.id == boss["distance_parameter"]
        ),
        None,
    )
    spec = DocumentSpec(
        source_sketch.name,
        depth.name if depth else "unusedLength",
        parameter_mm(depth) if depth else 1.0,
        ProfileKind="cuboid" if boss else "rectangle",
        SketchName=source_sketch.name,
        WidthMm=dimensions["width_mm"]["value_mm"],
        DepthMm=dimensions["height_mm"]["value_mm"],
        ConstrainRectangle=True,
        WidthParamName="width_mm",
        DepthParamName="height_mm",
    )
    target = MakeFusionDoc(spec)
    target.AssertValid()
    return target


def target_boss(source, target, measured, source_boss):
    source_depth = unique(
        (
            row
            for row in source.parameters
            if row.id == source_boss["distance_parameter"]
        ),
        "source boss parameter",
    )
    target_step = unique(
        (row for row in target.feature_timeline if row.operation),
        "constructor first solid operation",
    )
    params = {row.id: row for row in target.parameters}
    target_depth = params[target_step.definition.AlongParameterId]
    user = params[target_depth.expression.parameter_ids[0]]
    require(
        source_boss["direction"] == (0.0, 0.0, 1.0)
        and source_boss["signed_depth_mm"] > 0.0
        and parameter_mm(user)
        == parameter_mm(source_depth)
        == source_boss["signed_depth_mm"]
        and user.name == source_depth.name
        and target_step.operation == "create"
        and target_step.input_feature_ids == ("sketch",)
        and len(source.bodies) == len(target.bodies) == 1,
        "Expected a positively directed first blind solid with the verified depth",
    )
    return {
        "source": {
            **source_boss,
            "depth_parameter": trace(source_depth),
            "depth_parameter_spans": provenance(source_depth.provenance),
        },
        "constructor": {
            "step_id": target_step.id,
            "operation": str(target_step.operation),
            "definition": type(target_step.definition).__name__,
            "bound_profile": target.sketches[0].closed_profile_entity_ids,
            "depth_parameter": trace(target_depth),
            "user_parameter": trace(user),
            "taper_parameter": trace(params[target_step.definition.TaperParameterId]),
        },
        "geometry": {
            "expected_prism_volume_mm3": measured["dimensions"]["width_mm"]["value_mm"]
            * measured["dimensions"]["height_mm"]["value_mm"]
            * source_boss["signed_depth_mm"],
            "constructor_volume_mm3": target.bodies[0].topology.volume,
        },
    }


def map_case(recipe, variant, asset, observed, snapshot, tolerances):
    phase, measurement = observed
    raw, source = load_public(snapshot, asset, "solidworks")
    require(
        source.source.sha256 == asset["sha256"] and phase == "separate_process_reopen",
        "Source archive or measurement phase differs",
    )
    measured = rectangle_side(
        source, measurement, "solidworks", recipe, None, tolerances
    )
    source_sketch = measured["sketch"]
    frame = measured["frame"]
    basis = (xyz(frame.origin), xyz(frame.x_axis), xyz(frame.y_axis), xyz(frame.z_axis))
    require(
        basis == ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "Only the exact positive XY principal sketch enters the constructor comparison",
    )
    boss = (
        solidworks_boss(source, source_sketch, frame, raw, tolerances)
        if recipe == "P03"
        else None
    )
    target = constructor(source, measured, boss)
    (target_sketch,) = target.sketches
    (target_plane,) = target.support_planes
    target_edges = tuple(
        (
            row.id,
            (
                world(target_plane.transform, row.geometry.start),
                world(target_plane.transform, row.geometry.end),
            ),
        )
        for row in target_sketch.entities
        if isinstance(row.geometry, LineGeometry)
    )
    tolerance = tolerances["length_mm_absolute"]
    perimeter = match_perimeters(measured["perimeter"], target_edges, tolerance)
    require(
        perimeter["status"] == "equal",
        "Constructor perimeter does not match the measured source",
    )
    links = dict(perimeter["matched_links"])
    target_axes = {
        rule.references[0].entity_id: rule.kind
        for rule in target_sketch.constraints
        if rule.kind in ("horizontal", "vertical")
    }
    require(
        {links[key]: rule for key, rule in measured["axes"].items()} == target_axes,
        "Constructor line axes do not match the verified source operands",
    )
    (source_loop,) = source_sketch.closed_profile_entity_ids
    (target_loop,) = target_sketch.closed_profile_entity_ids
    require(
        frozenset(links[key] for key in source_loop) == frozenset(target_loop),
        "Constructor neutral perimeter membership differs",
    )
    fixed = [row.id for row in target_sketch.entities if row.fixed]
    require(
        len(fixed) == 1
        and not any(rule.kind == "coincident" for rule in target_sketch.constraints),
        "Constructor anchor representation changed",
    )
    unresolved = [
        [row.id, row.name, row.definition.type_id]
        for row in source.feature_timeline
        if isinstance(row.definition, NativeFeatureDefinition)
    ]
    require(
        unresolved and not FusionWriter().Supports(source, "review.f3d"),
        "Public source admission or unresolved history changed",
    )
    result = {
        "recipe": recipe,
        "variant": variant,
        "source": {
            "path": asset["path"],
            "sha256": asset["sha256"],
            "measurement_phase": phase,
            "sketch_id": source_sketch.id,
            "native_support_name": measured["native_support_name"],
            "support_plane_id": source_sketch.support_plane_id,
            "unresolved_native_feature_definitions": unresolved,
        },
        "perimeter": {
            "relation": perimeter,
            "source_loop": source_loop,
            "constructor_loop": target_loop,
            "source_axis_relations": measured["axes"],
            "constructor_axis_relations": target_axes,
            "source_inferred_endpoint_coincidences": measured["inferred_coincidences"],
        },
        "dimensions": axis_bindings(source, measured, target, links, tolerance),
        "anchor": {
            "source_origin_coincidence": measured["origin"],
            "constructor_fixed_point": fixed[0],
        },
        "constructor_parameter_inventory": [trace(row) for row in target.parameters],
    }
    if boss:
        result["boss"] = target_boss(source, target, measured, boss)
    return result


def report():
    snapshot = GitSnapshot(ROOT)
    raw = snapshot.blob(REVISION, SPECIFICATION)
    require(sha256(raw) == SPECIFICATION_SHA256, "Pinned recipe specification differs")
    specification = snapshot.parse_document(raw, SPECIFICATION)
    cases, receipts = [], {}
    for recipe_id, variants in VARIANTS.items():
        recipe = unique(
            (row for row in specification["recipes"] if row["id"] == recipe_id),
            "authorized rectangular discovery recipe",
        )
        receipt, sources, measurements = capture(
            snapshot, recipe, "solidworks", specification
        )
        receipts[recipe_id] = {
            "capture": receipt["receipt"],
            "measurements": receipt["measurements"],
        }
        for variant in variants:
            cases.append(
                map_case(
                    recipe_id,
                    variant,
                    sources[variant],
                    measurements[variant],
                    snapshot,
                    specification["comparison_tolerances"],
                )
            )
    return {
        "schema": 1,
        "source_capture_revision": REVISION,
        "scope": "positive XY rectangle and first blind boss",
        "status": "unqualified constructor mapping",
        "source_admitted_to_fusion_writer": False,
        "native_archive_generated": False,
        "receipts": receipts,
        "cases": cases,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
