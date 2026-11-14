from convert.adapters.Fusion.Native.Graph.GraphChecks import EmptyFields, ResolveField
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    MappingItems,
    ObjectFields,
    SeriesItems,
)
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.KnownHistory import KKnownHistory
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair


def CheckOperations(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    History: KKnownHistory,
    ProgenitorCount: int = 5,
) -> None:
    Manager = ResolveField(
        Graph, Context.Fragment, "rFeatureIdManager", "DcFeatureIdManager"
    )
    Forward = {
        IntegerValue(Entry.First): IntegerValue(Entry.Second)
        for Entry in MappingItems(Manager.Fields["featureIdMap"])
    }
    Reverse = {
        IntegerValue(Entry.First): tuple(
            IntegerValue(Value) for Value in SeriesItems(Entry.Second)
        )
        for Entry in MappingItems(Manager.Fields["enetityIdMap"])
    }
    if set(Reverse) != {
        Context.SketchFeature.ObjectId,
        Context.Extrude.ObjectId,
    } or Forward != {
        Operation: Entity
        for Entity, Operations in Reverse.items()
        for Operation in Operations
    }:
        raise ValueError("Native feature operation maps are not reciprocal")
    EmptyFields(Manager, ("obsoleteFeatureIds",))
    if Forward.get(History.Identity.OperationId) != Context.Extrude.ObjectId:
        raise ValueError("Native history body operation belongs to another feature")
    Table = ResolveField(Graph, Context.Extrude, "rProgenitorTable", "ProgenitorTable")
    Pairs = SeriesItems(Table.Fields["ProgenitorTagVec"])
    if len(Pairs) != ProgenitorCount or any(
        not isinstance(PairValue, ValuePair) for PairValue in Pairs
    ):
        raise ValueError("Native extrusion has an unsupported progenitor mapping count")
    Bodies = tuple(
        PairValue
        for PairValue in Pairs
        if isinstance(PairValue, ValuePair)
        and Graph.Resolve(PairValue.First).ClassName == "BodyProgenitor"
    )
    if len(Bodies) != 1 or Bodies[0].Second != History.Identity.SecondaryId:
        raise ValueError(
            "Native history secondary identity disagrees with body progenitor"
        )
    Progenitor = Graph.Resolve(Bodies[0].First)
    if Progenitor.Fields["bodyUuid"] != Context.DcBody.Fields["bodyUuid"]:
        raise ValueError("Native body progenitor UUID disagrees with modeled body")
    Occurrences = MappingItems(Progenitor.Fields["featureTagOccMap"])
    if (
        len(Occurrences) != 1
        or ObjectFields(Occurrences[0].First)["operationId"]
        != History.Identity.OperationId
    ):
        raise ValueError("Native body progenitor operation disagrees with history")
