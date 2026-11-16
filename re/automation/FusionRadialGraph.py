# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace
from importlib import import_module
from math import dist, isclose
from unittest.mock import patch

from PairedCaptureIntake import require
from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import (
    KDiaDimension,
    KRadiusDimension,
)
from convert.adapters.Fusion.Native.Circular.CheckSketchOnly import CheckSketchOnly
from convert.adapters.Fusion.Native.Circular.ReadCircle import ReadCircle
from convert.adapters.Fusion.Native.Circular.Snapshots.CheckCircular import (
    CheckCircular,
)
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    NumberValue,
    ObjectFields,
    PointCoords,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.ReadNames import ReadNames
from convert.adapters.Fusion.Native.Graph.SelectSketch import SelectSketch
from convert.adapters.Fusion.Native.Parameters.ParamExpression import ParamExpression
from convert.adapters.Fusion.Native.Policy.CheckAuxiliary import CheckSceneRefs
from convert.adapters.Fusion.Native.Policy.CheckGraph import CheckBase
from convert.adapters.Fusion.Native.Policy.CheckScopes import CheckScopes
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation

# The two measured classes have different archive payload, annotation and length semantics.
SPECS = {
    "FusionSketchDiameterDim": (
        KDiaDimension,
        "DiameterDimensionInfo",
        65536,
        "diameter",
        2,
        216,
    ),
    "FusionSketchRadialDim": (
        KRadiusDimension,
        "RadialDimensionInfo",
        131072,
        "radius",
        1,
        82,
    ),
}


# Scope catalog registration to this graph build so public class dispatch stays intact.
def registered_graph(model):
    catalog = ReadCatalog().Classes
    additions = []
    for name, (guid, *_) in SPECS.items():
        (schema,) = catalog[guid]
        require(schema.SchemaVersion == 0, "Unexpected radial dimension schema version")
        additions.append(NativeSchema(name, "Fusion", schema))
    schemas = ReadNames() + tuple(additions)
    build = import_module("convert.adapters.Fusion.Native.Graph.BuildGraph")
    with patch.object(build, "ReadNames", return_value=schemas):
        graph = build.BuildGraph(model)
    require(
        not any(
            group.Opaque
            for node in graph.Nodes.values()
            if node.SegmentId == 0
            for group in node.Groups
        ),
        "Design graph contains opaque groups",
    )
    return graph, schemas


# Keep altered validation views and negative cases separate from the parsed source graph.
def change_field(graph, node, name, value):
    groups = []
    changes = 0
    for group in node.Groups:
        fields = []
        for field in group.Fields:
            if field.FieldName == name:
                field = replace(field, Value=value)
                changes += 1
            fields.append(field)
        groups.append(replace(group, Fields=tuple(fields)))
    require(changes == 1, f"Expected one typed field {node.ClassName}.{name}")
    members = dict(graph.Nodes)
    members[(node.SegmentId, node.ObjectId)] = replace(node, Groups=tuple(groups))
    return replace(graph, Nodes=members)


# Require the native dimension, parameter, owner and dynamic update to agree by identity.
def radial_links(graph):
    context = SelectSketch(graph)
    dimensions = tuple(node for name in SPECS for node in graph.ByClass(name))
    require(len(dimensions) == 1, "Expected one typed circular dimension")
    dimension = dimensions[0]
    (binding,) = graph.ByClass("DcDoubleParameter")
    (parameter,) = graph.ByClass("Parameter")
    update = ResolveField(graph, binding, "rDynamicUpdateData", "DynamicUpdateData")
    circle = graph.OneClass("CircArc3D")
    sketch_ref = LocalRef(context.Sketch.ObjectId)
    feature_ref = LocalRef(context.SketchFeature.ObjectId)
    binding_ref = LocalRef(binding.ObjectId)
    SameNodes((dimension,), LinkedNodes(graph, context.Sketch, "dimensions"))
    SameNodes((binding,), LinkedNodes(graph, context.SketchFeature, "dcParameters"))
    dimension_fields = dimension.Fields
    require(
        dimension_fields["ParentNode"] == dimension_fields["rParent"] == sketch_ref
        and dimension_fields["dcParameter"] == binding_ref,
        "Dimension owner or model binding differs",
    )
    require(
        SeriesItems(dimension_fields["geometries"]) == (LocalRef(circle.ObjectId),),
        "Dimension does not target the sole circular curve",
    )
    RequireFields(
        dimension, {"isSick": False, "rClientObject": None, "isVisible": False}
    )
    require(
        parameter.Fields["dcParameter"] == binding_ref
        and binding.Fields["parameter"] == LocalRef(parameter.ObjectId)
        and binding.Fields["rrOwnerFeature"]
        == binding.Fields["rParentFeature"]
        == feature_ref,
        "Model parameter and sketch-feature binding are not reciprocal",
    )
    RequireFields(binding, {"isActive": True, "isEdited": False, "isEliminated": False})
    require(
        update.Fields["rOwnerNode"] == binding_ref
        and binding.Fields["rDynamicUpdateData"] == LocalRef(update.ObjectId),
        "Dynamic update data does not return to its binding",
    )
    RequireFields(
        update,
        {
            "bodies": ValueMap(()),
            "predecessors": ValueMap(()),
            "isBodyOK": False,
            "isPredecessorOK": False,
            "xRefPredecessorsHash": 0,
        },
    )
    plane = ResolveField(graph, context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix")
    SameNodes(
        (*graph.ByClass("EntityDataRef"), plane, binding),
        LinkedNodes(graph, context.SketchFeature, "childNodes"),
    )
    table = ResolveField(graph, context.Component, "rParameterTable", "ParameterTable")
    SameNodes((parameter,), LinkedNodes(graph, table, "children"))
    index = ResolveField(
        graph, table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    name = TextValue(parameter.Fields["userName"])
    RequireFields(
        index,
        {"parameterMap": ValueMap((ValuePair(name, LocalRef(parameter.ObjectId)),))},
    )
    slot = binding.Fields["rparamId"]
    require(
        type(slot) is int
        and slot
        == context.Fragment.Fields["nextParamId"]
        == table.Fields["highWaterMark"]
        == 1,
        "Sketch model parameter allocation differs",
    )
    return context, dimension, binding, parameter, update, circle


# Resolve the exact length and reference state from both the typed dimension and its binding.
def verify_dimension(dimension, binding, parameter, circle):
    _, info_key, native_code, kind, multiple, prefix = SPECS[dimension.ClassName]
    RequireFields(dimension, {"constraintType": native_code})
    data = ObjectFields(dimension.Fields[info_key])
    mode = data["bDriven"]
    require(
        type(mode) is bool and parameter.Fields["isDriven"] is mode,
        "Dimension and model parameter driving modes disagree",
    )
    RequireFields(
        parameter,
        {
            "isUserDefined": False,
            "isDirty": False,
            "isOrphan": False,
            "expressionType": 0,
            "booleanValue": False,
            "textValue": "",
            "unit": "mm",
        },
    )
    require(
        parameter.Fields.get("isExternal", False) is False,
        "Dimension has an external model parameter",
    )
    center = PointCoords(data["centerPoint"])
    carrier = circle.Fields["arcCurve"]
    saved_radius = NumberValue(ObjectFields(carrier)["radius"])
    require(
        data["arcToDim"] == carrier
        and center == PointCoords(ObjectFields(carrier)["center"])
        and data["needExtendArcForDim"] is False
        and data["hasTextPoint"] is True
        and TextValue(data["prefix"]) == chr(prefix),
        "Dimension's saved circular carrier or annotation differs",
    )
    sheet = ObjectFields(data["plane"])
    text_position = PointCoords(data["textPosition"])
    chord_point = PointCoords(data["chordPoint"])
    require(
        sheet["normalReversed"] is False
        and PointCoords(sheet["origin"]) == (0.0, 0.0, 0.0)
        and PointCoords(sheet["uAxis"]) == (1.0, 0.0, 0.0)
        and PointCoords(sheet["vAxis"]) == (0.0, 1.0, 0.0)
        and text_position[2] == chord_point[2] == 0.0,
        "Circular dimension layout is outside the verified XY plane",
    )
    amount = NumberValue(parameter.Fields["value"])
    require(
        saved_radius > 0
        and isclose(
            amount, NumberValue(binding.Fields["value"]), abs_tol=1e-9, rel_tol=1e-10
        ),
        "Circular dimension binding value differs",
    )
    SameNumbers(
        (NumberValue(data["radius"]), dist(center, chord_point), amount),
        (saved_radius, saved_radius, multiple * saved_radius),
    )
    name = TextValue(parameter.Fields["userName"])
    expression = ParamExpression(parameter, {name: parameter})
    require(
        name
        and not expression.parameter_ids
        and TextValue(data["text"]) == expression.source,
        "Dimension text does not identify its independent model parameter",
    )
    return kind, mode, name, amount, expression


# Check the original snapshot and scope after reusing structural checks on the verified additions.
def structural_circle(model, graph, schemas, context, dimension):
    proof = import_module("convert.adapters.Fusion.Native.Policy.CheckClasses")
    with (
        patch.object(proof, "ReadNames", return_value=schemas),
        patch.object(proof, "KDesignClasses", proof.KDesignClasses | frozenset(SPECS)),
    ):
        view = change_field(graph, context.Sketch, "dimensions", ValueSeries(()))
        sketch = view.Nodes[(0, context.Sketch.ObjectId)]
        children = SeriesItems(context.Sketch.Fields["children"])
        reference = LocalRef(dimension.ObjectId)
        require(
            children.count(reference) == 1,
            "Circular dimension is missing from its sketch children",
        )
        view = change_field(
            view,
            sketch,
            "children",
            ValueSeries(tuple(row for row in children if row != reference)),
        )
        view = change_field(
            view, context.SketchFeature, "dcParameters", ValueSeries(())
        )
        visible = SelectSketch(view)
        CheckBase(view, visible)
        shape = ReadCircle(view, visible)
    CheckScopes(graph, context, model.Asset.AssetId)
    CheckSketchOnly(graph, context, model)
    require(len(model.Snapshots) == 1, "Expected one saved circular sheet snapshot")
    CheckCircular(model, shape, None, None)
    CheckSceneRefs(graph, model.Graphics)
    return shape


# Publish inspectable semantics only after the graph and saved sheet both pass their checks.
def verified_circle(model, graph, schemas):
    context, dimension, binding, raw_parameter, update, circle = radial_links(graph)
    kind, driven, name, amount, expression = verify_dimension(
        dimension, binding, raw_parameter, circle
    )
    shape = structural_circle(model, graph, schemas, context, dimension)
    parameter = Parameter(
        raw_parameter.Identity,
        name,
        ParameterValue(amount * 10.0, ValueKind.KLength, "mm"),
        role=ParameterRole.KReference if driven else ParameterRole.KDriving,
        expression=expression,
        owner_id=context.SketchFeature.Identity,
    )
    relation = SketchRelation(
        dimension.Identity,
        kind,
        (ConstraintRef(circle.Identity),),
        parameter_id=parameter.id,
        driving=not driven,
    )
    return (
        context,
        shape,
        parameter,
        relation,
        (dimension, binding, raw_parameter, update),
    )
