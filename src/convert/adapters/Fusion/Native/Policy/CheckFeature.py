from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


def CheckFeature(Graph: NativeGraph, NodeValue: NativeNode) -> None:
    RequireFields(
        NodeValue,
        {
            "isActive": True,
            "isEdited": False,
            "isEliminated": False,
            "bDisabled": False,
            "isSuppressed": False,
            "isImplicitlySuppressed": False,
            "isZombieFeature": False,
            "rGroupRepresentative": None,
            "rParentFeature": None,
            "rReferencedContext": None,
        },
    )
    EmptyFields(NodeValue, ("groupMembers",))
    Status = ResolveField(Graph, NodeValue, "status", "DcStatus")
    RequireFields(Status, {"statusType": 0})
    EmptyFields(Status, ("statusCodes",))
