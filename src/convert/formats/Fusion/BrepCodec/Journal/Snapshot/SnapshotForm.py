from collections import deque as MakeQueue
from typing import TypeAlias

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.RelinkSubtypes import (
    RelinkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken

KSpliceTable: TypeAlias = dict[tuple[int, int], int]


def IsSnapshotDrop(Entities: tuple[KJournalEntity, ...], Index: int) -> bool:
    Value = Entities[Index]
    if isinstance(Value, TrackAttrib):
        return True
    if not isinstance(Value, (TimeAttrib, TagAttrib)):
        return False
    Owner = Value.Links.OwnerRef
    if not 0 < Owner < len(Entities):
        raise ValueError("Fusion snapshot attribute names a missing owner")
    return isinstance(Entities[Owner], BodyNode)


def AttribChain(Records: tuple[AsmRecord, ...], Owner: int) -> tuple[int, ...]:
    Chain: list[int] = []
    Current = Records[Owner].Tokens[0][1]
    while type(Current) is int and Current > 0:
        if Current in Chain or Current >= len(Records):
            raise ValueError("Fusion snapshot attribute chain repeats or leaves")
        Chain.append(Current)
        Current = Records[Current].Tokens[2][1]
    return tuple(Chain)


def ChainSplices(Records: tuple[AsmRecord, ...], Drops: frozenset[int]) -> KSpliceTable:
    Splices: KSpliceTable = {}
    for Owner in range(1, len(Records)):
        Chain = () if Owner in Drops else AttribChain(Records, Owner)
        KeptItems = tuple(Value for Value in Chain if Value not in Drops)
        if len(KeptItems) == len(Chain):
            continue
        Splices[(Owner, 0)] = KeptItems[0] if KeptItems else -1
        for Ordinal, Value in enumerate(KeptItems):
            Later = Ordinal + 1 < len(KeptItems)
            Splices[(Value, 2)] = KeptItems[Ordinal + 1] if Later else -1
            Splices[(Value, 3)] = KeptItems[Ordinal - 1] if Ordinal else -1
    return Splices


def SnapshotTarget(
    Index: int, SlotField: tuple[int, int], Drops: frozenset[int], Splices: KSpliceTable
) -> int:
    Target = Splices.get((Index, SlotField[0]), SlotField[1])
    return -1 if Target < 0 or Target in Drops else Target


def SnapshotOrder(
    Entities: tuple[KJournalEntity, ...],
    Records: tuple[AsmRecord, ...],
    Drops: frozenset[int],
    Splices: KSpliceTable,
) -> tuple[int, ...]:
    Roots = tuple(
        Index for Index, Value in enumerate(Entities) if isinstance(Value, BodyNode)
    )
    Visited = set(Roots)
    Waiting = MakeQueue(Roots)
    Order = [0]
    while Waiting:
        Index = Waiting.popleft()
        Order.append(Index)
        for SlotIndex, (TagValue, Field) in enumerate(Records[Index].Tokens):
            if TagValue != 12 or type(Field) is not int:
                continue
            Target = SnapshotTarget(Index, (SlotIndex, Field), Drops, Splices)
            if Target >= len(Records):
                raise ValueError("Fusion snapshot reference leaves its table")
            if Target > 0 and Target not in Visited:
                Visited.add(Target)
                Waiting.append(Target)
    return tuple(Order)


def SnapshotToken(
    Index: int,
    SlotIndex: int,
    Token: KAsmToken,
    Drops: frozenset[int],
    Splices: KSpliceTable,
    Positions: dict[int, int],
) -> KAsmToken:
    TagValue, Field = Token
    if SlotIndex == 1 and TagValue == 4:
        return (TagValue, -1)
    if TagValue != 12 or type(Field) is not int:
        return Token
    Target = SnapshotTarget(Index, (SlotIndex, Field), Drops, Splices)
    return (TagValue, Positions[Target] if Target >= 0 else -1)


def SnapshotForm(
    Entities: tuple[KJournalEntity, ...],
) -> tuple[KJournalEntity, ...]:
    Leader = Entities[0] if Entities else None
    if not isinstance(Leader, AsmRoot) or Leader.Attribute >= 0:
        raise ValueError("Fusion snapshot form requires a plain leading ASM header")
    Records = tuple(MakeEntityNode(Value) for Value in Entities)
    Drops = frozenset(
        Index for Index in range(1, len(Entities)) if IsSnapshotDrop(Entities, Index)
    )
    Splices = ChainSplices(Records, Drops)
    Order = SnapshotOrder(Entities, Records, Drops, Splices)
    if len(Order) + len(Drops) != len(Entities):
        raise ValueError("Fusion snapshot form leaves an unreachable record")
    Positions = {Index: Ordinal for Ordinal, Index in enumerate(Order)}
    Relinked = tuple(MakeEntityNode(Value) for Value in RelinkSubtypes(Entities, Order))
    return tuple(
        ReadEntityNode(
            AsmRecord(
                Record.Name,
                tuple(
                    SnapshotToken(Index, SlotIndex, Token, Drops, Splices, Positions)
                    for SlotIndex, Token in enumerate(Record.Tokens)
                ),
            )
        )
        for Index, Record in zip(Order, Relinked, strict=True)
    )
