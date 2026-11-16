# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ProbeOrigin
from PairedCaptureIntake import require
from ProbeBossAuthor import DRIVERS, SIZE_OFFSETS
from convert.adapters.Fusion.Native.Graph.GraphChecks import LinkedNodes, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    PointCoords,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression


# Both the stored parameter parent and the feature binding must identify their intended record.
def checked_parameter(graph, table, owner, binding, slot, name, unit, amount):
    parameter = ResolveField(graph, binding, "parameter", "Parameter")
    update = ResolveField(graph, binding, "rDynamicUpdateData", "DynamicUpdateData")
    fields = parameter.Fields
    expression = f"{amount:g} mm" if unit == "mm" else "0.0 deg"
    quantity = amount / 10.0 if unit == "mm" else 0.0
    require(
        graph.Resolve(fields["rParent"]) == table
        and graph.Resolve(fields["dcParameter"]) == binding
        and graph.Resolve(binding.Fields["rrOwnerFeature"]) == owner
        and graph.Resolve(binding.Fields["rParentFeature"]) == owner
        and graph.Resolve(update.Fields["rOwnerNode"]) == binding
        and binding.Fields["isActive"] is True
        and binding.Fields["isEdited"] is binding.Fields["isEliminated"] is False
        and binding.Fields["rparamId"] == fields["creationIndex"] == slot
        and binding.Fields["value"] == fields["value"] == quantity
        and fields["isUserDefined"] is fields["isDriven"] is False
        and fields["isDirty"] is fields["isOrphan"] is False
        and fields.get("isExternal", False) is False
        and fields["unit"] == unit
        and fields["userName"] == name
        and fields["expression"] == expression
        and not ParamExpression(parameter, {name: parameter}).parameter_ids,
        f"Saved P03 feature ownership or literal parameter differs for {name}",
    )
    return parameter


# Check the two sketch bindings and the two separate Boss bindings from the emitted archive.
def inspect_parameters(graph, context, sizes):
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    helper = ResolveField(
        graph, table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    width, height = LinkedNodes(graph, context.SketchFeature, "dcParameters")
    matrix = ResolveField(
        graph, context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    (plane_ref,) = LinkedNodes(graph, matrix, "dataRefs")
    require(
        LinkedNodes(graph, context.SketchFeature, "childNodes")
        == (plane_ref, matrix, width, height),
        "P03 sketch child inventory does not identify its two direct bindings",
    )
    owners = (
        context.SketchFeature,
        context.SketchFeature,
        context.Extrude,
        context.Extrude,
    )
    bindings = (width, height, context.Along, context.Taper)
    names = (*DRIVERS, "d4")
    parameters = tuple(
        checked_parameter(graph, table, owner, binding, slot, name, unit, amount)
        for slot, (owner, binding, name, unit, amount) in enumerate(
            zip(
                owners,
                bindings,
                names,
                ("mm", "mm", "mm", "deg"),
                (*sizes, 0),
                strict=True,
            ),
            start=1,
        )
    )
    index = MappingItems(helper.Fields["parameterMap"])
    require(
        tuple(row.First for row in index) == tuple(sorted(names))
        and {row.First: graph.Resolve(row.Second) for row in index}
        == dict(zip(names, parameters, strict=True))
        and LinkedNodes(graph, table, "children") == parameters
        and set(graph.ByClass("Parameter")) == set(parameters)
        and set(graph.ByClass("DcDoubleParameter")) == set(bindings)
        and table.Fields["highWaterMark"] == context.Fragment.Fields["nextParamId"] == 4
        and tuple(subject.Target.ObjectId for subject in helper.Frame.Subjects or ())
        == (table.ObjectId, *(row.ObjectId for row in parameters)),
        "P03 parameter table, name index or native allocator differs",
    )
    return {
        name: {
            "parameter_id": parameter.ObjectId,
            "binding_id": binding.ObjectId,
            "owner_id": owner.ObjectId,
            "slot": parameter.Fields["creationIndex"],
            "unit": parameter.Fields["unit"],
            "value_native": parameter.Fields["value"],
            "expression": parameter.Fields["expression"],
        }
        for name, parameter, binding, owner in zip(
            names, parameters, bindings, owners, strict=True
        )
    }


# Compare independently decoded raw subject/rank metadata with typed dimension and anchor links.
def inspect_sketch_rules(content, graph, context, parameters):
    members, rules, anchor, raw_dims = ProbeOrigin.native_records(content)
    require(
        anchor["owner"] == context.Sketch.ObjectId
        and {
            node.ObjectId for node in LinkedNodes(graph, context.Sketch, "constraints")
        }
        == rules.keys(),
        "The emitted P03 sketch does not own its anchored rules",
    )
    settings = graph.OneClass("CommonDataAssetSettings").ObjectId
    dimensions = LinkedNodes(graph, context.Sketch, "dimensions")
    require(
        len(dimensions) == 2
        and {node.ObjectId for node in dimensions} == raw_dims.keys(),
        "The emitted P03 sketch does not own exactly two size dimensions",
    )
    proof = []
    for ordinal, (name, node) in enumerate(zip(DRIVERS[:2], dimensions, strict=True)):
        deps, ranks, props = ProbeOrigin.ReadRulePrefix(
            ProbeOrigin.MetaCursor(raw_dims[node.ObjectId])
        )
        subjects = tuple(
            (row.Target.ObjectId, row.ObserverIndex)
            for row in node.Frame.Subjects or ()
        )
        fields = node.Fields
        require(
            subjects == tuple(zip(deps, ranks, strict=True))
            and deps[0] == settings
            and ranks[0] == ordinal
            and props == {"EntityGenesis": 0}
            and fields["ParentNode"] == fields["rParent"]
            and graph.Resolve(fields["rParent"]) == context.Sketch
            and fields["dcParameter"].ObjectId == parameters[name]["binding_id"],
            f"P03 dimension {name} raw subjects or owner differs",
        )
        proof.append(
            {
                "id": node.ObjectId,
                "code": fields["constraintType"],
                "arguments": tuple(
                    row.ObjectId for row in SeriesItems(fields["geometries"])
                ),
                "dependencies": deps[1:],
                "ranks": ranks[1:],
                "settings_rank": ranks[0],
                "cached_measurement": inspect_linear_cache(
                    graph, node, parameters[name], SIZE_OFFSETS[ordinal]
                ),
            }
        )
    anchor_node = graph.Nodes[(0, anchor["id"])]
    require(
        tuple(
            (row.Target.ObjectId, row.ObserverIndex)
            for row in anchor_node.Frame.Subjects or ()
        )
        == tuple(zip(anchor["dependencies"], anchor["ranks"], strict=True)),
        "P03 typed anchor does not agree with its saved subject ranks",
    )
    ProbeOrigin.check_ranks(proof, anchor)
    return {"anchor": anchor, "dimensions": proof, "design_members": members}


# Reconstruct the saved annotation from the exact typed endpoints and literal parameter.
def inspect_linear_cache(graph, dimension, parameter, offset):
    fields = dimension.Fields
    info = ObjectFields(fields["LinearDimensionInfo"])
    start, end = (
        PointCoords(graph.Resolve(row).Fields["point"])
        for row in SeriesItems(fields["geometries"])
    )
    shifted_start = tuple(
        value + delta for value, delta in zip(start, offset, strict=True)
    )
    shifted_end = tuple(value + delta for value, delta in zip(end, offset, strict=True))
    middle = tuple(
        (first + second) / 2.0
        for first, second in zip(shifted_start, shifted_end, strict=True)
    )
    plane = ObjectFields(info["plane"])
    require(
        info["bDriven"] is fields["isSick"] is False
        and info["length"] == parameter["value_native"]
        and info["prefix"] == ""
        and info["text"] == parameter["expression"]
        and PointCoords(info["startPoint"])
        == PointCoords(info["extnStartPoint"])
        == start
        and PointCoords(info["endPoint"]) == end
        and PointCoords(info["DimStartPoint"]) == shifted_start
        and PointCoords(info["DimEndPoint"]) == shifted_end
        and PointCoords(info["textPosition"]) == middle
        and plane["normalReversed"] is False
        and PointCoords(plane["origin"]) == (0.0, 0.0, 0.0)
        and PointCoords(plane["uAxis"]) == (1.0, 0.0, 0.0)
        and PointCoords(plane["vAxis"]) == (0.0, 1.0, 0.0),
        "P03 direct dimension scalar or ordered endpoint cache differs",
    )
    return {
        "text": info["text"],
        "value_cm": info["length"],
        "ordered_endpoints_cm": (start, end),
    }
