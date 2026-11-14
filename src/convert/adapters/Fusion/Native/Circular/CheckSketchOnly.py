from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


def CheckSketchOnly(
    Graph: NativeGraph, Context: SketchContext, Model: DocumentModel
) -> None:
    if Model.Bodies or Graph.ByClass("Body") or Graph.ByClass("DcBody"):
        raise ValueError("Native sketch-only profile contains modeled bodies")
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    EmptyFields(Bodies, ("children", "groupChildren"))
    EmptyFields(Context.Fragment, ("dcBodies",))
    Serializer = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    EmptyFields(Serializer, ("mapBodyId",))
    if Serializer.Fields["partName"] != "":
        raise ValueError("Native sketch-only profile has a history part")
    Manager = ResolveField(
        Graph, Context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    Forward = MappingItems(Manager.Fields["featureIdMap"])
    Reverse = MappingItems(Manager.Fields["enetityIdMap"])
    if (
        len(Forward) != 1
        or len(Reverse) > 1
        or Forward[0].Second != Context.SketchFeature.ObjectId
        or (
            Reverse
            and (
                Reverse[0].First != Context.SketchFeature.ObjectId
                or SeriesItems(Reverse[0].Second) != (Forward[0].First,)
            )
        )
    ):
        raise ValueError("Native sketch-only operation maps disagree")
    _ = IntegerValue(Forward[0].First)
    EmptyFields(Manager, ("obsoleteFeatureIds",))
    Table = ResolveField(
        Graph, Context.SketchFeature, "rProgenitorTable", "ProgenitorTable"
    )
    EmptyFields(Table, ("ProgenitorTagVec",))
    SameNodes((), LinkedNodes(Graph, Context.Fragment, "dcBodies"))
    for ClassName in (
        "ModelDataRef",
        "SketchRegionRef",
        "SketchRegionRecipe",
        "SketchCurveProgenitor",
        "BodyProgenitor",
        "DcExtrudeToolBody",
    ):
        if Graph.ByClass(ClassName):
            raise ValueError(
                "Native sketch-only profile contains an unaccounted feature dependency"
            )
