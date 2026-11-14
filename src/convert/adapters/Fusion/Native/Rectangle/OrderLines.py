from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.adapters.Fusion.Native.Graph.GraphChecks import ResolveField


def OrderLines(
    Graph: NativeGraph, Lines: tuple[NativeNode, ...]
) -> tuple[NativeNode, ...]:
    Starts = {
        ResolveField(Graph, NodeValue, "rStartPoint", "Point3D").ObjectId: NodeValue
        for NodeValue in Lines
    }
    if len(Starts) != 4:
        raise ValueError("Native rectangle requires four distinct corner identities")
    First = min(Starts)
    Current = First
    Result: list[NativeNode] = []
    while len(Result) < 4:
        NodeValue = Starts.get(Current)
        if NodeValue is None or NodeValue in Result:
            raise ValueError(
                "Native rectangle endpoint links do not form one closed loop"
            )
        Result.append(NodeValue)
        Current = ResolveField(Graph, NodeValue, "rEndPoint", "Point3D").ObjectId
    if Current != First:
        raise ValueError("Native rectangle endpoint loop is not closed")
    return tuple(Result)
