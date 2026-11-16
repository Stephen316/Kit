# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from math import dist

from PairedCaptureIntake import require
from RectanglePairSketch import same
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.adapters.Fusion.Native.Policy.CheckExtrusion import CheckExtrusion
from convert.adapters.Fusion.Native.Policy.DesignClasses import KDesignClasses
from convert.adapters.Fusion.Native.Rectangle.CheckBodyJoins import CheckBodyJoins
from convert.adapters.Fusion.Native.Rectangle.CheckRegion import CheckRegion
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag


# A point record identity, rather than coordinate equality, is evidence of a shared native corner.
def inspect_corners(graph, context, sketch, lines, paired, tolerance):
    points = {node.ObjectId: node for node in graph.ByClass("Point3D")}
    geometries = {entity.id: entity for entity in sketch.entities}
    links = dict(paired["perimeter"]["matched_links"])
    perimeter = dict(paired["perimeter"]["fusion_world_mm"])
    counts = Counter()
    edges = []
    for line in lines:
        fields = line.Fields
        identity = f"fusion-sketch-entity-{line.ObjectId}"
        neutral = geometries[identity]
        endpoints = tuple(
            ResolveField(graph, line, key, "Point3D").ObjectId
            for key in ("rStartPoint", "rEndPoint")
        )
        require(
            graph.Resolve(fields["rParent"]) == context.Sketch
            and fields["isFixed"]
            is fields["isProjected"]
            is fields["isReference"]
            is False
            and neutral.attributes["fusion.line_native_point_ids"] == endpoints
            and neutral.attributes["fusion.entity_tag"] == CurveTag(line),
            "Fusion edge ownership, endpoint identity or tag differs from its partial projection",
        )
        for point_id, expected in zip(endpoints, perimeter[identity], strict=True):
            source = PointCoords(points[point_id].Fields["point"])
            same(
                tuple(value * 10 for value in source),
                expected,
                tolerance,
                f"{identity} saved endpoint",
            )
        counts.update(endpoints)
        edges.append(
            {
                "fusion_line": line.ObjectId,
                "ordered_point_ids": endpoints,
                "curve_tag": CurveTag(line),
                "solidworks_edge": links[identity],
            }
        )
    rules = LinkedNodes(graph, context.Sketch, "constraints")
    (anchor,) = [rule for rule in rules if rule.Fields["constraintType"] == 1]
    corner, origin = LinkedNodes(graph, anchor, "geometries")
    require(
        len(lines) == len(counts) == 4
        and set(counts.values()) == {2}
        and set(points) == {*counts, origin.ObjectId}
        and corner.ObjectId in counts
        and all(
            graph.Resolve(node.Fields["rParent"]) == context.Sketch
            for node in points.values()
        )
        and origin.Fields["isFixed"] is origin.Fields["isOrigin"] is True
        and corner.Fields["isFixed"] is corner.Fields["isOrigin"] is False
        and PointCoords(origin.Fields["point"])
        == PointCoords(corner.Fields["point"])
        == (0, 0, 0)
        and graph.Resolve(anchor.Fields["ParentNode"]) == context.Sketch,
        "Fusion anchor no longer binds a free shared corner to its distinct fixed Origin",
    )
    axes = {
        row["fusion_line"]: paired["axes"]["fusion"][
            f"fusion-sketch-entity-{row['fusion_line']}"
        ]
        for row in edges
    }
    require(
        len(rules) == 5
        and {rule.ObjectId for rule in rules}
        == {rule.ObjectId for rule in graph.ByClass("SketchGeomConstraint")}
        and {
            LinkedNodes(graph, rule, "geometries")[0].ObjectId: rule.Fields[
                "constraintType"
            ]
            for rule in rules
            if rule is not anchor
        }
        == {
            identity: {"horizontal": 64, "vertical": 128}[kind]
            for identity, kind in axes.items()
        },
        "Fusion saved axis constraints do not bind the same paired sides",
    )
    return {
        "edges": edges,
        "corner_incidence": sorted(counts.items()),
        "anchor": {
            "relation": anchor.ObjectId,
            "free_corner": corner.ObjectId,
            "fixed_origin": origin.ObjectId,
        },
        "native_axis_rules": axes,
    }


# Resolve every saved model parameter through its own feature binding and dynamic update.
def inspect_drivers(graph, context, document):
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    index = ResolveField(
        graph, table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    parameters = LinkedNodes(graph, table, "children")
    catalog = {node.Fields["userName"]: node for node in parameters}
    projected = {row.name: row for row in document.parameters}
    names = ("width_mm", "height_mm", "depth_mm", "d4")
    sketch_step, boss_step = document.feature_timeline
    require(
        tuple(catalog) == names
        and set(projected) == set(names)
        and table.Fields["highWaterMark"] == context.Fragment.Fields["nextParamId"] == 4
        and {
            row.First: graph.Resolve(row.Second)
            for row in MappingItems(index.Fields["parameterMap"])
        }
        == catalog,
        "Fusion parameter allocation or name index differs",
    )
    width, height = LinkedNodes(graph, context.SketchFeature, "dcParameters")
    bindings = (width, height, context.Along, context.Taper)
    owners = (
        context.SketchFeature,
        context.SketchFeature,
        context.Extrude,
        context.Extrude,
    )
    result = {}
    for slot, (name, binding, owner) in enumerate(
        zip(names, bindings, owners, strict=True), start=1
    ):
        parameter = catalog[name]
        fields = parameter.Fields
        update = ResolveField(graph, binding, "rDynamicUpdateData", "DynamicUpdateData")
        literal = ParamExpression(parameter, catalog)
        actual = projected[name]
        require(
            graph.Resolve(fields["rParent"]) == table
            and graph.Resolve(fields["dcParameter"]) == binding
            and graph.Resolve(binding.Fields["parameter"]) == parameter
            and graph.Resolve(binding.Fields["rrOwnerFeature"]) == owner
            and graph.Resolve(binding.Fields["rParentFeature"]) == owner
            and graph.Resolve(update.Fields["rOwnerNode"]) == binding
            and fields["creationIndex"] == binding.Fields["rparamId"] == slot
            and fields["value"] == binding.Fields["value"] == actual.value.value
            and fields["isUserDefined"] is fields["isDriven"] is False
            and not fields.get("isExternal", False)
            and actual.expression == literal
            and not literal.parameter_ids
            and actual.attributes["fusion.binding_id"] == binding.ObjectId
            and actual.id == f"fusion-parameter-{parameter.ObjectId}"
            and actual.owner_id == (sketch_step if slot <= 2 else boss_step).id
            and actual.role.value == "reference",
            f"{name} does not retain the proven native owner, dependency-free literal and observed neutral role",
        )
        result[name] = {
            "slot": slot,
            "parameter_object": parameter.ObjectId,
            "binding_object": binding.ObjectId,
            "owner_feature": owner.ObjectId,
            "dynamic_update": update.ObjectId,
            "native_is_driven": fields["isDriven"],
            "native_unit": fields["unit"],
            "stored_value": fields["value"],
            "literal": literal.source,
            "literal_parameter_ids": literal.parameter_ids,
            "neutral_id": actual.id,
            "neutral_owner": actual.owner_id,
            "neutral_role": actual.role.value,
            "neutral_unit": actual.value.unit,
        }
    require(
        result["d4"]["native_unit"] == "deg" and result["d4"]["stored_value"] == 0,
        "Fusion retained zero taper changed",
    )
    return result


# Measure each dimension by its actual ordered native operands, retaining stale annotation data.
def inspect_dimensions(graph, context, corners, drivers, paired, tolerance, variant):
    rows = LinkedNodes(graph, context.Sketch, "dimensions")
    require(
        len(rows) == 2,
        "Fusion scoped rectangle does not have two native size dimensions",
    )
    bound = {}
    for name, node, code in zip(
        ("width_mm", "height_mm"), rows, (1 << 22, 1 << 23), strict=True
    ):
        fields = node.Fields
        raw = ObjectFields(fields["LinearDimensionInfo"])
        points = LinkedNodes(graph, node, "geometries")
        ids = tuple(point.ObjectId for point in points)
        (edge,) = [
            edge
            for edge in corners["edges"]
            if set(edge["ordered_point_ids"]) == set(ids)
        ]
        observed = paired["dimensions"][name]
        normalized = observed["fusion"]
        world = tuple(
            tuple(value * 10 for value in PointCoords(point.Fields["point"]))
            for point in points
        )
        require(
            fields["constraintType"] == code
            and fields["ParentNode"] == fields["rParent"]
            and graph.Resolve(fields["rParent"]) == context.Sketch
            and graph.Resolve(fields["dcParameter"]).ObjectId
            == drivers[name]["binding_object"]
            and f"fusion-sketch-dimension-{node.ObjectId}" == normalized["relation_id"]
            and edge["solidworks_edge"] == observed["solidworks"]["perimeter_id"]
            and raw["bDriven"] is False
            and raw["prefix"] == ""
            and raw["text"] == drivers[name]["literal"]
            and raw["length"] == drivers[name]["stored_value"]
            and abs(dist(*world) - normalized["value_mm"]) <= tolerance,
            f"Fusion saved {name} driver, axis, exact edge or operand measurement differs",
        )
        for first, second in zip(world, normalized["operands_world_mm"], strict=True):
            same(first, second, tolerance, f"{name} ordered source endpoints")
        cached = {
            name: PointCoords(raw[name])
            for name in ("startPoint", "endPoint", "extnStartPoint")
        }
        for key, point in zip(("startPoint", "endPoint"), points, strict=True):
            same(
                cached[key],
                PointCoords(point.Fields["point"]),
                tolerance / 10,
                f"{name} {key}",
            )
        stale = dist(cached["extnStartPoint"], cached["startPoint"]) * 10
        expected = 3.0 if (variant, name) == ("edit-height_mm-23", "height_mm") else 0.0
        require(
            abs(stale - expected) <= tolerance,
            "Unexpected native annotation cache discrepancy",
        )
        bound[name] = {
            "dimension_object": node.ObjectId,
            "ordered_operands": ids,
            "operands_world_mm": world,
            "fusion_edge": edge["fusion_line"],
            "solidworks_edge": edge["solidworks_edge"],
            "counterpart_operand_order": observed["ordered_operands"],
            "annotation_anchors_cm": cached,
            "annotation_extension_delta_mm": stale,
        }
    return bound


# Require the actual saved prism and region while reporting native auxiliaries outside the target contract.
def inspect_native(raw, document, paired, tolerances):
    model = ReadDocument(raw)
    graph = BuildGraph(model)
    context = SelectExtrusion(graph)
    lines = graph.ByClass("Line3D")
    (sketch,) = document.sketches
    CheckRegion(graph, context, lines, model.Asset.AssetId)
    CheckExtrusion(graph, context)
    history = CheckBodyJoins(graph, context, model)
    require(
        isinstance(history, PrismHistory),
        "Fusion positive XY body does not retain a typed prism history",
    )
    tolerance = tolerances["length_mm_absolute"]
    corners = inspect_corners(
        graph, context, sketch, lines, paired["rectangle"], tolerance
    )
    drivers = inspect_drivers(graph, context, document)
    dimensions = inspect_dimensions(
        graph,
        context,
        corners,
        drivers,
        paired["rectangle"],
        tolerance,
        paired["variant"],
    )
    boss = paired["boss"]["fusion"]
    step = document.feature_timeline[-1]
    members = boss["selected_entities"]
    require(
        set(members) == {f"fusion-sketch-entity-{line.ObjectId}" for line in lines}
        and PointCoords(context.Extrude.Fields["profileNormal"]) == (0, 0, 1)
        and drivers["depth_mm"]["stored_value"] > 0
        and step.definition.TaperParameterId == drivers["d4"]["neutral_id"],
        "Fusion selected region, positive world extent or explicit taper differs",
    )
    return {
        "profile": {
            "native_sketch": context.Sketch.ObjectId,
            "boss": context.Extrude.ObjectId,
            "selection_proxy": boss["native_profile_proxy"],
            "selection_descriptor": boss["native_profile_descriptor"],
            "selected_native_members": step.attributes["fusion.profile_native_members"],
            "selected_neutral_members": members,
            **corners,
        },
        "direct_parameters": drivers,
        "dimensions": dimensions,
        "strict_unmodeled_design_classes": dict(
            sorted(
                Counter(
                    node.ClassName
                    for node in graph.Nodes.values()
                    if node.SegmentId == 0 and node.ClassName not in KDesignClasses
                ).items()
            )
        ),
        "saved_native_inventory": {
            "history_part": model.Bodies[0].PartName,
            "history_type": type(history).__name__,
            "prism_mm": (
                history.Model.Width,
                history.Model.Depth,
                history.Model.Height,
            ),
            "snapshots": [
                (part.Name, type(part.Snapshot).__name__) for part in model.Snapshots
            ],
            "has_graphics": model.Graphics is not None,
            "configurations": len(model.Configurations),
        },
    }
