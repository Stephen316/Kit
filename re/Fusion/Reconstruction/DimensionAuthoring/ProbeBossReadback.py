# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose, prod

from PairedCaptureIntake import require
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.CheckFeature import CheckFeature
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckShape
from convert.adapters.Fusion.Native.Policy.CheckMassCache import CheckMassCache
from convert.adapters.Fusion.Native.Rectangle.CheckBodyJoins import CheckBodyJoins
from convert.adapters.Fusion.Native.Rectangle.CheckOperations import CheckOperations
from convert.adapters.Fusion.Native.Rectangle.CheckPrismTags import CheckPrismTags
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag, SketchTag
from convert.adapters.Fusion.Native.Rectangle.OrderLines import OrderLines
from convert.adapters.Fusion.Native.Rectangle.ReadLine import ReadLine
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry


# Expose actual ordered geometry without dropping the separately verified dimension records.
def rectangle_shape(graph, context, rules):
    lines = OrderLines(graph, graph.ByClass("Line3D"))
    points = graph.ByClass("Point3D")
    dimensions = LinkedNodes(graph, context.Sketch, "dimensions")
    children = LinkedNodes(graph, context.Sketch, "children")
    SameNodes(children, (*lines, *points, *dimensions))
    require(
        len(lines) == 4
        and len(points) == 5
        and all(
            graph.Resolve(item.Fields["rParent"]) == context.Sketch for item in children
        )
        and {item.ObjectId for item in dimensions}
        == {row["id"] for row in rules["dimensions"]},
        "The emitted P03 sketch has an unexpected child or geometry owner",
    )
    geometry = tuple(ReadLine(graph, row) for row in lines)
    xs = {row.start.x for row in geometry}
    ys = {row.start.y for row in geometry}
    require(
        len(xs) == len(ys) == 2
        and min(xs) == min(ys) == 0.0
        and sum(row.start.x * row.end.y - row.end.x * row.start.y for row in geometry)
        > 0,
        "The emitted P03 profile is outside the anchored positive XY winding",
    )
    return RectGeometry((), geometry, lines, max(xs), max(ys), (0.0, 0.0, 0.0))


# The saved Boss must own the exact typed region selecting the measured sketch edges.
def inspect_selected_profile(graph, context, shape, asset_id):
    CheckRegion(graph, context, shape.LineNodes, asset_id)
    (model_ref,) = LinkedNodes(graph, context.Extrude, "profileDataRefs")
    (region,) = LinkedNodes(graph, model_ref, "dataRefs")
    recipe = ResolveField(graph, region, "rRecipe", "SketchRegionRecipe")
    tool = ResolveField(graph, context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody")
    SameNodes(
        LinkedNodes(graph, context.Extrude, "childNodes"),
        (model_ref, region, context.Along, context.Taper, tool),
    )
    require(
        all(
            graph.Resolve(node.Fields["rParentFeature"]) == context.Extrude
            for node in (model_ref, region, tool)
        ),
        "P03 selected region, proxy and tool must belong to the same Boss",
    )
    (region_value,) = SeriesItems(recipe.Fields["skRegionRecipe"])
    (loop,) = SeriesItems(ObjectFields(region_value)["faceRecipe"])
    tags = tuple(SketchTag(value, 0) for value in SeriesItems(loop.First))
    tags_to_lines = {CurveTag(node): node.ObjectId for node in shape.LineNodes}
    members = tuple(tags_to_lines[tag] for tag in tags)
    require(
        members == tuple(row.ObjectId for row in shape.LineNodes),
        "The emitted P03 recipe is not in its directed perimeter order",
    )
    return {
        "sketch": context.Sketch.ObjectId,
        "profile_proxy": model_ref.ObjectId,
        "region": region.ObjectId,
        "recipe": recipe.ObjectId,
        "outer": loop.Second,
        "tags": tags,
        "ordered_line_members": members,
    }


# Check dependency order and edge typing using nodes recovered from their actual semantic links.
def inspect_dependencies(graph, context, parameters, profile):
    matrix = ResolveField(
        graph, context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (plane_ref,) = LinkedNodes(graph, matrix, "dataRefs")
    tool = ResolveField(graph, context.Extrude, "rExtrudeToolBody", "DcExtrudeToolBody")
    component = graph.OneClass("DcComponent").ObjectId
    width = parameters["width_mm"]["binding_id"]
    height = parameters["height_mm"]["binding_id"]
    sketch, boss = context.SketchFeature.ObjectId, context.Extrude.ObjectId
    plane, mat = plane_ref.ObjectId, matrix.ObjectId
    region, model_ref = profile["region"], profile["profile_proxy"]
    along, taper, body_tool = (
        context.Along.ObjectId,
        context.Taper.ObjectId,
        tool.ObjectId,
    )
    order = (
        component,
        plane,
        mat,
        width,
        height,
        sketch,
        region,
        model_ref,
        along,
        taper,
        body_tool,
        boss,
    )
    expected = {
        (component, sketch, 4096),
        (component, boss, 4096),
        (plane, mat, 1),
        (mat, sketch, 1),
        (width, sketch, 1),
        (height, sketch, 1),
        (sketch, region, 4),
        (region, model_ref, 1),
        (model_ref, body_tool, 1),
        (along, body_tool, 1),
        (taper, body_tool, 1),
        (body_tool, boss, 1),
    }
    compute = ResolveField(
        graph, context.Fragment, "rComputeManager", "DcComputeManager"
    )
    deps = ResolveField(
        graph, context.Fragment, "rDependencyManager", "DcDependencyManager"
    )
    require(
        compute.Fields["sortIsCurrent"] is deps.Fields["mapsAreCurrent"] is True
        and tuple(row.ObjectId for row in LinkedNodes(graph, compute, "sortedNodesAll"))
        == order
        and edge_set(graph, deps, "successorMap") == expected
        and edge_set(graph, deps, "predecessorMap")
        == {(dst, src, kind) for src, dst, kind in expected},
        "The emitted P03 compute roster or reciprocal typed dependencies differ",
    )
    for target in order:
        node = graph.Nodes[(0, target)]
        update = ResolveField(graph, node, "rDynamicUpdateData", "DynamicUpdateData")
        expected_inputs = {src for src, dst, _ in expected if dst == target}
        if expected_inputs:
            expected_inputs.add(target)
        entries = MappingItems(update.Fields["predecessors"])
        require(
            tuple(row.First.ObjectId for row in entries)
            == tuple(sorted(expected_inputs))
            and all(row.Second == update.Fields["timeStamp"] for row in entries)
            and graph.Resolve(update.Fields["rOwnerNode"]) == node,
            "The emitted P03 dependency update closure differs",
        )
    return {"compute_order": order, "edges": sorted(expected)}


# Resolve both ends of each saved dependency and refuse duplicates before comparing memberships.
def edge_set(graph, node, name):
    rows = MappingItems(node.Fields[name])
    result = [
        (
            graph.Resolve(row.First).ObjectId,
            graph.Resolve(pair.First).ObjectId,
            pair.Second,
        )
        for row in rows
        for pair in MappingItems(row.Second)
    ]
    require(len(result) == len(set(result)), "Duplicate P03 dependency edge")
    return set(result)


# Validate the saved first feature, one BRep prism and its geometry and inertial cache.
def inspect_body(graph, context, model, shape, sizes, measured, tolerances):
    CheckFeature(graph, context.SketchFeature)
    CheckFeature(graph, context.Extrude)
    CheckExtrusion(graph, context)
    history = CheckBodyJoins(graph, context, model)
    require(isinstance(history, PrismHistory), "P03 requires one saved prism history")
    CheckOperations(graph, context, history)
    CheckPrismTags(graph, context, shape, history)
    CheckShape(context, shape, history)
    CheckMassCache(context, history)
    prism = history.Model
    vertices = [
        tuple(value * 10 for value in corner) for corner in history.Frame.CornersCm
    ]
    low = tuple(min(axis) for axis in zip(*vertices, strict=True))
    high = tuple(max(axis) for axis in zip(*vertices, strict=True))
    nominal = prism.Width, prism.Depth, prism.Height
    topology = len(history.Frame.Planes), len(history.Frame.Edges), len(vertices)
    cache = ObjectFields(context.BodyNode.Fields["cache"])
    centroid = tuple(value * 10 for value in PointCoords(cache["cog"]))
    volume = prod(nominal)
    require(
        len(model.Bodies) == measured["body_count"] == 1
        and context.Extrude.Fields["featureUserName"] == "BlindBoss"
        and topology == (6, 12, 8)
        and close_axes(nominal, sizes, tolerances["length_mm_absolute"])
        and close_axes(low, (0, 0, 0), tolerances["length_mm_absolute"])
        and close_axes(high, sizes, tolerances["length_mm_absolute"])
        and close_axes(
            centroid, measured["center_of_mass_mm"], tolerances["length_mm_absolute"]
        )
        and isclose(
            volume,
            measured["volume_mm3"],
            rel_tol=0,
            abs_tol=tolerances["volume_mm3_absolute"],
        ),
        "The emitted P03 body differs from the independently reopened source measurements",
    )
    return {
        "body_count": len(model.Bodies),
        "solid": context.BodyNode.ObjectId,
        "owner": context.Extrude.ObjectId,
        "history_part": model.Bodies[0].PartName,
        "history_state": (
            context.Extrude.Fields["startModelHS"],
            context.Extrude.Fields["endModelHS"],
        ),
        "operation": "new_body",
        "operation_code": context.Extrude.Fields["booleanOperation"],
        "axis": PointCoords(context.Extrude.Fields["profileNormal"]),
        "extent": "one_sided_positive_blind_from_profile_plane",
        "bounds_mm": (low, high),
        "topology_faces_edges_vertices": topology,
        "volume_mm3": volume,
        "cache_volume_mm3": cache["volume"] * 1000.0,
        "cache_area_mm2": cache["area"] * 100.0,
        "cache_centroid_mm": centroid,
        "cache_inertia_cm5": PointCoords(cache["moi"]),
        "cache_cross_terms_cm5": PointCoords(cache["moiOffDiag"]),
        "inertial_cache_consistency": "verified_against_prism_geometry",
        "source_body": {
            key: measured[key]
            for key in ("body_count", "volume_mm3", "center_of_mass_mm")
        },
        "material_scope": "generated default; physical density and mass parity unqualified",
    }


# Reuse the physical source tolerance for each spatial axis in the saved record.
def close_axes(actual, expected, tolerance):
    return all(
        isclose(x, y, rel_tol=0, abs_tol=tolerance)
        for x, y in zip(actual, expected, strict=True)
    )
