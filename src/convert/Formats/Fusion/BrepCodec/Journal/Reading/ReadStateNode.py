from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadBoardsMut import ReadBoardsMut
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsStateFlagMut import (
    IsStateFlagMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.CheckFieldEnd import (
    CheckFieldEnd,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


# the state node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadStateNode(Record: AsmRecord) -> DeltaState:
    Cursor = FieldCursor(Record)
    StateId = ReadLongMut(Cursor)
    Backward = IsStateFlagMut(Cursor)
    Hidden = IsStateFlagMut(Cursor)
    PreviousNode = ReadRefMut(Cursor)
    NextNode = ReadRefMut(Cursor)
    PartnerNode = ReadRefMut(Cursor)
    MergedWith = ReadRefMut(Cursor)
    OwnerStream = ReadRefMut(Cursor)
    NameValue = ReadTextMut(Cursor) if IsLogicalMut(Cursor) else None
    Boards = ReadBoardsMut(Cursor)
    StateLinks = tuple(ReadRefMut(Cursor) for _ in range(ReadCountMut(Cursor, 256)))
    CheckFieldEnd(Cursor)
    return DeltaState(
        StateId,
        Backward,
        Hidden,
        PreviousNode,
        NextNode,
        PartnerNode,
        MergedWith,
        OwnerStream,
        NameValue,
        Boards,
        StateLinks,
    )
