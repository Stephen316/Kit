# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Circular.RadialBinding import RadialBinding
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# both native owners and the operand must agree to establish a dimension on the sole circle
def ReadSizeLinks(
    Graph: NativeGraph, Context: SketchContext, Dimension: NativeNode
) -> RadialBinding:
    Circle = Graph.OneClass("CircArc3D")
    Binding = Graph.OneClass("DcDoubleParameter")
    Parameter = Graph.OneClass("Parameter")
    SketchRef = LocalRef(Context.Sketch.ObjectId)
    FeatureRef = LocalRef(Context.SketchFeature.ObjectId)
    BindingRef = LocalRef(Binding.ObjectId)
    SameNodes(LinkedNodes(Graph, Context.Sketch, "dimensions"), (Dimension,))
    SameNodes(LinkedNodes(Graph, Context.SketchFeature, "dcParameters"), (Binding,))
    RequireFields(
        Dimension,
        {
            "ParentNode": SketchRef,
            "rParent": SketchRef,
            "dcParameter": BindingRef,
            "isSick": False,
            "rClientObject": None,
            "isVisible": False,
        },
    )
    if SeriesItems(Dimension.Fields["geometries"]) != (LocalRef(Circle.ObjectId),):
        raise ValueError("Native radial dimension must target the sole circular curve")
    Nodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    RequireFields(
        Binding,
        {
            "parameter": LocalRef(Parameter.ObjectId),
            "rrOwnerFeature": FeatureRef,
            "rParentFeature": FeatureRef,
            "rParent": LocalRef(Nodes.ObjectId),
            "rGroupRepresentative": None,
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
        },
    )
    RequireFields(Parameter, {"dcParameter": BindingRef})
    Update = ResolveField(Graph, Binding, "rDynamicUpdateData", "DynamicUpdateData")
    RequireFields(
        Update,
        {
            "rOwnerNode": BindingRef,
            "isBodyOK": False,
            "isPredecessorOK": False,
            "xRefPredecessorsHash": 0,
        },
    )
    EmptyFields(Update, ("bodies", "predecessors"))
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    SameNodes(
        LinkedNodes(Graph, Context.SketchFeature, "childNodes"),
        (*Graph.ByClass("EntityDataRef"), Matrix, Binding),
    )
    CheckSizeTable(Graph, Context, Binding, Parameter)
    return RadialBinding(Dimension, Binding, Parameter, Update, Circle)


# the count allocator and native name index must identify the same sole model parameter
def CheckSizeTable(
    Graph: NativeGraph,
    Context: SketchContext,
    Binding: NativeNode,
    Parameter: NativeNode,
) -> None:
    Table = ResolveField(Graph, Context.Component, "rParameterTable", "ParameterTable")
    SameNodes(LinkedNodes(Graph, Table, "children"), (Parameter,))
    RequireFields(Parameter, {"rParent": LocalRef(Table.ObjectId)})
    Index = ResolveField(
        Graph, Table, "rParameterSearchByNameHelper", "ParameterSearchByNameHelper"
    )
    Names = MappingItems(Index.Fields["parameterMap"])
    NameValue = TextValue(Parameter.Fields["userName"])
    if (
        not NameValue
        or len(Names) != 1
        or Names[0].First != NameValue
        or Names[0].Second != LocalRef(Parameter.ObjectId)
    ):
        raise ValueError("Native radial dimension parameter name index disagrees")
    SlotValue = IntegerValue(Binding.Fields["rparamId"])
    if not (
        SlotValue
        == IntegerValue(Context.Fragment.Fields["nextParamId"])
        == IntegerValue(Table.Fields["highWaterMark"])
        == 1
    ):
        raise ValueError("Native radial dimension parameter allocation disagrees")
