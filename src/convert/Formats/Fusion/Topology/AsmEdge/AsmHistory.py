from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import (
    ReadModelHead,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadStateNode import (
    ReadStateNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadStreamNode import (
    ReadStreamNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmLocation import AsmLocation
from convert.Formats.Fusion.Topology.AsmEdge.ReadAsmSection import ReadAsmSection
from convert.Formats.Fusion.Topology.AsmEdge.ReadSlotChanges import ReadSlotChanges
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmRecord,
    AsmTable,
    ReadAsmName,
    ReadAsmRecord,
)


# geometry and journal state slots belong to separate ordinal tables
@MakeDataClass(frozen=True, slots=True)
class AsmHistory:
    Initial: AsmTable
    Records: tuple[AsmRecord, ...]
    Locations: tuple[AsmLocation, ...]
    Changes: tuple[BulletinChange, ...]
    Earlier: tuple[BulletinChange, ...]
    LatestSite: AsmLocation


# both neighboring slots must agree before the later transition can expose stored revisions
def ReadAsmHistory(BlobData: bytes) -> AsmHistory:
    if len(BlobData) > 2 * 1024 * 1024:
        raise ValueError("Oversized Fusion ASM history evidence")
    Cursor = MetaCursor(BlobData)
    Header, _ = ReadModelHead(Cursor, True)
    if Header.IntWidth != 8 or Header.RootCount != 2:
        raise ValueError("Unsupported Fusion ASM history header")
    Initial, InitialSites = ReadAsmSection(Cursor, "Begin-of-ASM-History-Data")
    Stream = ReadStreamNode(ReadAsmRecord(Cursor, ReadAsmName(Cursor)))
    LatestSite = Cursor.Offset
    States: list[DeltaState] = []
    LatestEnd = LatestSite
    for SlotIndex in range(3):
        if ReadAsmName(Cursor) != "delta_state":
            raise ValueError("Missing Fusion ASM history state")
        States.append(ReadStateNode(ReadAsmRecord(Cursor, "delta_state")))
        if SlotIndex == 0:
            LatestEnd = Cursor.Offset
    if ReadAsmName(Cursor) != "End-of-ASM-History-Section":
        raise ValueError("Unexpected Fusion ASM history state count")
    Trailing, TrailingSites = ReadAsmSection(Cursor, "End-of-ASM-data")
    Latest, InitialState, Earlier = States
    if (
        Cursor.Offset != len(BlobData)
        or len(Initial) < 2
        or Initial[0].Name != "asmheader"
        or any(Record.Name == "asmheader" for Record in Initial[1:] + Trailing)
        or not Trailing
        or (
            Stream.WorkingNode,
            Stream.ActiveNode,
            Stream.InitialNode,
            Stream.OwnerEntity,
        )
        != (-1, 0, 1, -1)
        or Stream.MaxStatesToKeep != 0
        or not 0 <= InitialState.StateId < Earlier.StateId < Latest.StateId
        or not Latest.StateId == Stream.CurrentStateId == Stream.MaxStateId
    ):
        raise ValueError("Fusion ASM history sections or state identities disagree")
    Changes = ReadSlotChanges(Latest, 0, -1, 2)
    _ = ReadSlotChanges(InitialState, 1, 2, -1)
    EarlierChanges = ReadSlotChanges(Earlier, 2, 0, 1)
    return AsmHistory(
        AsmTable(Header.RootCount, Initial),
        Initial + Trailing,
        InitialSites + TrailingSites,
        Changes,
        EarlierChanges,
        AsmLocation(LatestSite, LatestEnd),
    )
