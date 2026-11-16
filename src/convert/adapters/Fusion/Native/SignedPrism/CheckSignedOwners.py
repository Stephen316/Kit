# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Rectangle.CheckSideRecipe import CheckSideRecipe
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the actual generic solid key and feature tag must agree with the saved design body
def CheckOwnTags(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shape: RectGeometry,
    History: JournalModel,
    Shell: PlanarShell,
    BodyTag: FeatureTag,
) -> tuple[int, dict[str, int]]:
    CheckSerializer(Graph, Context, Model, Shell)
    Operation = CheckActiveOp(Graph, Context, History, Shell, BodyTag)
    BodyValue, Secondary, Sides = ReadProgenitors(Graph, Context, Shape)
    Occurrences = MappingItems(BodyValue.Fields["featureTagOccMap"])
    if (
        BodyTag != FeatureTag(str(Operation), (), Secondary, 0)
        or BodyValue.Fields["bodyUuid"] != Context.DcBody.Fields["bodyUuid"]
        or len(Occurrences) != 1
        or ObjectFields(Occurrences[0].First)["operationId"] != Operation
    ):
        raise ValueError(
            "Native reverse prism body tag does not own the modeled extrusion"
        )
    return Operation, Sides


# serializer mapping links the live native key with the one modeled and parented body
def CheckSerializer(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Model: DocumentModel,
    Shell: PlanarShell,
) -> None:
    BodyValue = Context.BodyNode
    SameNodes((BodyValue,), Graph.ByClass("Body"))
    SameNodes((Context.DcBody,), Graph.ByClass("DcBody"))
    SameNodes((Context.DcBody,), LinkedNodes(Graph, Context.Fragment, "dcBodies"))
    if (
        Graph.Resolve(Context.DcBody.Fields["rOwnFeature"]) != Context.Extrude
        or Context.DcBody.Fields["bodyUuid"] != BodyValue.Fields["persistentId"]
    ):
        raise ValueError(
            "Native reverse prism body ownership or persistent identity disagrees"
        )
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    SameNodes((BodyValue,), LinkedNodes(Graph, Bodies, "children"))
    SameNodes((BodyValue,), LinkedNodes(Graph, Bodies, "groupChildren"))
    Serializer = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    RequireFields(Serializer, {"rBodies": LocalRef(Bodies.ObjectId), "rBody": None})
    Entries = MappingItems(Serializer.Fields["mapBodyId"])
    if (
        len(Entries) != 1
        or len(Model.Bodies) != 1
        or IntegerValue(Entries[0].First) != Shell.EntityTag
        or IntegerValue(Entries[0].Second) != BodyValue.ObjectId
        or Model.Bodies[0].PartName
        != "Breps.BlobParts/" + TextValue(Serializer.Fields["partName"])
    ):
        raise ValueError("Native reverse prism serializer does not own the live body")
    RequireFields(
        BodyValue, {"bodyType": 2, "rOwningDeriveFeature": None, "overriddenBody": None}
    )


# a body tag owns this operation through both the forward and reverse design indices
def CheckActiveOp(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    History: JournalModel,
    Shell: PlanarShell,
    BodyTag: FeatureTag,
) -> int:
    Feature = Context.Extrude
    Stream = History.Stream
    if (
        Shell.StateId != Feature.Fields["endModelHS"]
        or History.States[Stream.InitialNode].StateId != Feature.Fields["startModelHS"]
        or Stream.NextEntityTag <= Shell.EntityTag
        or not BodyTag.PrimaryId.isdecimal()
    ):
        raise ValueError(
            "Native reverse prism history state or operation identity disagrees"
        )
    Operation = int(BodyTag.PrimaryId)
    Manager = ResolveField(
        Graph, Context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    RequireFields(Manager, {"rOwnerFragment": LocalRef(Context.Fragment.ObjectId)})
    Forward = MappingItems(Manager.Fields["featureIdMap"])
    Reverse = MappingItems(Manager.Fields["enetityIdMap"])
    Index = {IntegerValue(Entry.First): IntegerValue(Entry.Second) for Entry in Forward}
    Owners = {IntegerValue(Entry.First): SeriesItems(Entry.Second) for Entry in Reverse}
    Pairs = [
        (IntegerValue(OperationKey), Owner)
        for Owner, OperationKeys in Owners.items()
        for OperationKey in OperationKeys
    ]
    if (
        len(Index) != len(Forward)
        or len(Owners) != len(Reverse)
        or set(Owners) != {Feature.ObjectId, Context.SketchFeature.ObjectId}
        or any(not OperationKeys for OperationKeys in Owners.values())
        or len(Pairs) != len(Index)
        or dict(Pairs) != Index
        or Index.get(Operation) != Feature.ObjectId
    ):
        raise ValueError("Native reverse prism operation map is not reciprocal")
    EmptyFields(Manager, ("obsoleteFeatureIds",))
    return Operation


# each side label comes from its saved curve recipe to retain its physical direction
def ReadProgenitors(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Shape: RectGeometry,
) -> tuple[NativeNode, int, dict[str, int]]:
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    BodyValue: list[tuple[NativeNode, int]] = []
    Sides: dict[str, int] = {}
    for Entry in SeriesItems(Table.Fields["ProgenitorTagVec"]):
        if not isinstance(Entry, ValuePair):
            raise ValueError("Malformed native reverse prism progenitor mapping")
        Owner = Graph.Resolve(Entry.First)
        Label = IntegerValue(Entry.Second)
        if Owner.ClassName == "BodyProgenitor":
            BodyValue.append((Owner, Label))
        elif Owner.ClassName == "SketchCurveProgenitor" and str(Label) not in Sides:
            Recipe = ResolveField(Graph, Owner, "rRecipe", "SketchCurveRecipe")
            Sides[str(Label)] = CheckSideRecipe(
                Recipe.Fields["profileEdgeTagData"], Shape
            )
        else:
            raise ValueError("Unknown or duplicate native reverse prism progenitor")
    if (
        len(BodyValue) != 1
        or set(Sides) != {"3", "4", "5", "6"}
        or len(set(Sides.values())) != 4
    ):
        raise ValueError(
            "Native reverse prism progenitors do not cover the selected rectangle"
        )
    return *BodyValue[0], Sides
