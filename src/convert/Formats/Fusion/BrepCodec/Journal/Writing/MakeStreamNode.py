from convert.Formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import IntWord, RefWord
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the stream node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeStreamNode(Value: StreamState) -> AsmRecord:
    Numbers = (
        Value.CurrentStateId,
        Value.MaxStateId,
        Value.MaxStatesToKeep,
        Value.NextEntityTag,
    )
    References = (
        Value.WorkingNode,
        Value.ActiveNode,
        Value.InitialNode,
        Value.OwnerEntity,
    )
    return AsmRecord(
        "history_stream", (*map(IntWord, Numbers), *map(RefWord, References))
    )
