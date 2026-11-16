# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose, prod
import re


# Preserve the actual selected profile objects before checking their physical perimeter.
def selected_profile(design, sketch, boss, adsk, same, require):
    value = boss.profile
    profile = adsk.fusion.Profile.cast(value)
    if profile is None:
        items = adsk.core.ObjectCollection.cast(value)
        require(
            items is not None and items.count == 1, "Boss did not select one profile"
        )
        profile = adsk.fusion.Profile.cast(items.item(0))
    require(
        profile is not None
        and profile.isOnSketchPlane
        and sketch.profiles.count == 1
        and same(design, profile, sketch.profiles.item(0))
        and same(design, profile.parentSketch, sketch)
        and profile.profileLoops.count == 1,
        "Boss profile does not resolve to the sole owned sketch profile",
    )
    loop = profile.profileLoops.item(0)
    curves = loop.profileCurves
    require(
        loop.isOuter and curves.count == sketch.sketchCurves.count == 4,
        "Native Boss needs one four-line outer loop",
    )
    indices = []
    for index in range(curves.count):
        curve = adsk.fusion.SketchLine.cast(curves.item(index).sketchEntity)
        require(
            curve is not None and same(design, curve.parentSketch, sketch),
            "Profile curve belongs to another sketch",
        )
        matching = [
            offset
            for offset in range(sketch.sketchCurves.count)
            if same(design, curve, sketch.sketchCurves.item(offset))
        ]
        require(len(matching) == 1, "Native profile member did not resolve uniquely")
        indices.append(matching[0])
    require(
        sorted(indices) == list(range(4)),
        "Selected Boss loop changed its sketch membership",
    )
    return {
        "loop_count": profile.profileLoops.count,
        "selected_sketch": sketch.name,
        "outer": loop.isOuter,
        "sketch_curve_indices": indices,
    }


# Bind native depth and taper parameters and distinguish a blind New Body from cached geometry.
def boss_facts(design, boss, adsk, same, require):
    extent = adsk.fusion.DistanceExtentDefinition.cast(boss.extentOne)
    require(
        extent is not None and extent.distance is not None,
        "Boss extent is not a native blind distance",
    )
    depth = extent.distance
    taper = boss.taperAngleOne
    parameters = design.allParameters
    require(
        depth == parameters.itemByName("depth_mm")
        and taper is not None
        and taper == parameters.itemByName("d4")
        and same(design, depth.createdBy, boss)
        and same(design, taper.createdBy, boss),
        "Boss depth or taper does not resolve to its exact owned model parameter",
    )
    start_faces, end_faces = boss.startFaces, boss.endFaces
    bodies = design.rootComponent.bRepBodies
    require(
        start_faces is not None
        and end_faces is not None
        and start_faces.count
        == end_faces.count
        == bodies.count
        == boss.bodies.count
        == 1
        and same(design, bodies.item(0), boss.bodies.item(0)),
        "Boss output body or end caps changed identity",
    )
    return {
        "operation": (
            "new_body"
            if boss.operation == adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            else "unresolved"
        ),
        "single_sided": not boss.hasTwoExtents
        and boss.extentTwo is None
        and boss.symmetricExtent is None,
        "from_profile_plane": adsk.fusion.ProfilePlaneStartDefinition.cast(
            boss.startExtent
        )
        is not None,
        "solid": boss.isSolid,
        "thin": boss.isThinExtrude,
        "depth_driver": depth.name,
        "depth_mm": depth.value * 10.0,
        "taper_driver": taper.name,
        "taper_radians": taper.value,
        "body_count": boss.bodies.count,
        "start_cap_z_mm": start_faces.item(0).pointOnFace.z * 10.0,
        "end_cap_z_mm": end_faces.item(0).pointOnFace.z * 10.0,
    }


# Bind each generic before/after/edited snapshot to the actual feature and profile identities.
def snapshot(fresh, helper, contract, document, label):
    design = helper["design_of"](document)
    root = design.rootComponent
    extrusions = root.features.extrudeFeatures
    require = contract["require"]
    require(
        root.sketches.count == extrusions.count == 1
        and design.timeline.markerPosition == design.timeline.count,
        "P03 requires one live sketch and Boss at the end of the timeline",
    )
    sketch, boss = root.sketches.item(0), extrusions.item(0)
    sketch_name, boss_name = contract["FEATURES"]
    require(
        sketch.name == sketch_name
        and boss.name == boss_name
        and sketch.referencePlane == root.xYConstructionPlane
        and sketch.timelineObject.index == 0
        and boss.timelineObject.index == 1,
        "P03 native timeline, name or principal XY datum differs",
    )
    reading = fresh["measure"](helper, document, label)
    shared = helper["adsk"], fresh["same_entity"], require
    reading["boss"] = boss_facts(design, boss, *shared)
    reading["boss_profile"] = selected_profile(design, sketch, boss, *shared)
    return reading


# Stage measurements must keep live owned sketch operands, literals and the sole solid.
def check_snapshot(reading, sizes, orientations, shape, contract):
    require = contract["require"]
    width, height, depth = sizes
    feature_names = contract["FEATURES"]
    timeline = reading["feature_tree"]
    require(
        reading["design_type"] == "parametric"
        and [row["name"] for row in timeline] == list(feature_names)
        and [row["type"] for row in timeline] == ["Sketch", "ExtrudeFeature"]
        and [row["index"] for row in timeline] == [0, 1]
        and all(
            row["health"]["state"] == "healthy"
            and not row["health"]["message"]
            and row["suppressed"] is False
            and row["rolled_back"] is False
            for row in timeline
        ),
        "P03 native history is unhealthy or does not preserve its ordered features",
    )
    (sketch,) = reading["sketches"]
    (area,) = sketch["profile_areas_mm2"]
    close = shape["close_mm"]
    require(
        sketch["support"] == "ConstructionPlane"
        and sketch["fully_constrained"] is True
        and isclose(area, width * height, rel_tol=0, abs_tol=1e-3),
        "P03 live profile area or XY sketch differs",
    )
    binding = sketch["bindings"]
    origin, corners, axes = shape["perimeter"](sketch, binding, width, height)
    shape["check_relations"](binding, origin, corners, axes)
    shape["check_dimensions"](
        reading, binding, "owned", sizes[:2], corners, orientations
    )
    profile = reading["boss_profile"]
    require(
        profile["loop_count"] == 1
        and profile["selected_sketch"] == feature_names[0]
        and profile["outer"] is True
        and sorted(profile["sketch_curve_indices"]) == list(range(4)),
        "P03 Boss no longer selects the exact owned sketch loop",
    )
    expressions = check_parameters(reading, sizes, close, contract)
    check_body(reading, sizes, close, require)
    return expressions


# Verify literal values from the complete retained native model parameter inventory.
def check_parameters(reading, sizes, close, contract):
    require = contract["require"]
    names = (*contract["EDITS_MM"], "d4")
    values = dict(zip(names, (*sizes, 0.0), strict=True))
    rows = reading["parameters"]
    params = {row["name"]: row for row in rows}
    require(
        len(params) == len(rows) and set(params) == values.keys(),
        "P03 parameter inventory is incomplete or ambiguous",
    )
    for name, value in values.items():
        row = params[name]
        unit = "deg" if name == "d4" else "mm"
        require(
            row["kind"] == "ModelParameter"
            and row["unit"] == unit
            and not row["dependencies"]
            and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?\s+" + unit, row["expression"])
            and close(row["value_internal"] * (10.0 if unit == "mm" else 1.0), value),
            f"P03 native parameter does not keep its independent literal: {name}",
        )
    return {name: params[name]["expression"] for name in names}


# Confirm the positive blind extent and native mass-property geometry at every stage.
def check_body(reading, sizes, close, require):
    boss = reading["boss"]
    depth = sizes[2]
    (body,) = reading["bodies"]
    low, high = body["bounding_box_mm"]
    require(
        boss["operation"] == "new_body"
        and boss["single_sided"] is boss["from_profile_plane"] is boss["solid"] is True
        and boss["thin"] is False
        and boss["depth_driver"] == "depth_mm"
        and boss["taper_driver"] == "d4"
        and close(boss["depth_mm"], depth)
        and close(boss["taper_radians"], 0.0)
        and close(boss["start_cap_z_mm"], 0.0)
        and close(boss["end_cap_z_mm"], depth)
        and reading["body_count"] == boss["body_count"] == 1
        and body["solid"] is True
        and (body["faces"], body["edges"], body["vertices"]) == (6, 12, 8)
        and reading["mass_properties"] == "measured"
        and isclose(reading["volume_mm3"], prod(sizes), rel_tol=1e-8, abs_tol=1e-3)
        and isclose(
            body["volume_mm3"], reading["volume_mm3"], rel_tol=1e-8, abs_tol=1e-3
        )
        and all(close(a, b) for a, b in zip(low, (0, 0, 0), strict=True))
        and all(close(a, b) for a, b in zip(high, sizes, strict=True))
        and all(
            close(a, b / 2.0)
            for a, b in zip(reading["center_of_mass_mm"], sizes, strict=True)
        ),
        "P03 native Boss operation, extent, topology or measured body differs",
    )
