from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBoards import MakeBoards
from convert.formats.Fusion.BrepCodec.Journal.Writing.StateFlag import StateFlag
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import IntWord, RefWord
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def MakeStateNode(Value: DeltaState) -> AsmRecord:
    References = (
        Value.PreviousNode,
        Value.NextNode,
        Value.PartnerNode,
        Value.MergedWith,
        Value.OwnerStream,
    )
    NameFields: tuple[KAsmToken, ...] = (
        ((11, None),) if Value.NameValue is None else ((10, None), (7, Value.NameValue))
    )
    Fields: tuple[KAsmToken, ...] = (
        IntWord(Value.StateId),
        IntWord(StateFlag(Value.RollsBack)),
        IntWord(StateFlag(Value.Hidden)),
        *map(RefWord, References),
        *NameFields,
        *MakeBoards(Value.Boards),
        IntWord(len(Value.StateLinks)),
        *map(RefWord, Value.StateLinks),
    )
    return AsmRecord("delta_state", Fields)
