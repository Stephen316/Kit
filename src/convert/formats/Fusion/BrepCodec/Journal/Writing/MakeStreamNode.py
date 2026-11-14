from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import IntWord, RefWord
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


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
