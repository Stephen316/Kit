from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import MappingItems, TextValue
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.adapters.Fusion.Native.Graph.KnownHistory import KKnownHistory
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


def CheckBodyJoins(
    Graph: NativeGraph, Context: ExtrudeContext, Model: DocumentModel
) -> KKnownHistory:
    BodyValue = Context.BodyNode
    SameNodes((BodyValue,), Graph.ByClass("Body"))
    SameNodes((Context.DcBody,), Graph.ByClass("DcBody"))
    SameNodes((Context.DcBody,), LinkedNodes(Graph, Context.Fragment, "dcBodies"))
    if (
        Graph.Resolve(Context.DcBody.Fields["rOwnFeature"]) != Context.Extrude
        or Context.DcBody.Fields["bodyUuid"] != BodyValue.Fields["persistentId"]
    ):
        raise ValueError("Native body ownership or persistent identity disagrees")
    Bodies = ResolveField(Graph, Context.Component, "rBodies", "Bodies")
    SameNodes((BodyValue,), LinkedNodes(Graph, Bodies, "children"))
    SameNodes((BodyValue,), LinkedNodes(Graph, Bodies, "groupChildren"))
    Serializer = ResolveField(Graph, Bodies, "rBRepSerializer", "BRepHistorySerializer")
    Entries = MappingItems(Serializer.Fields["mapBodyId"])
    if (
        len(Model.Bodies) != 1
        or len(Entries) != 1
        or Entries[0].Second != BodyValue.ObjectId
    ):
        raise ValueError("Native body serializer does not map the sole modeled body")
    History = Model.Bodies[0].History
    if not isinstance(
        History, (PrismHistory, HistoryModel, FrustumHistory)
    ) or Model.Bodies[0].PartName != "Breps.BlobParts/" + TextValue(
        Serializer.Fields["partName"]
    ):
        raise ValueError("Native extrusion requires its qualified typed history part")
    if History.Identity.BodyKey != IntegerValue(Entries[0].First):
        raise ValueError("Native history body key disagrees with the serializer map")
    if (
        History.History.CurrentStateId != History.History.CurrentId
        or History.History.MaxStateId != History.History.CurrentId
        or History.History.NextEntityTag <= History.Identity.BodyKey
        or History.History.BoardStatus != 2
        or History.History.InitialId != Context.Extrude.Fields["startModelHS"]
        or History.History.CurrentId != Context.Extrude.Fields["endModelHS"]
    ):
        raise ValueError("Native extrusion history-state boundaries disagree")
    RequireFields(
        BodyValue, {"bodyType": 2, "rOwningDeriveFeature": None, "overriddenBody": None}
    )
    return History
