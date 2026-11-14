from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.StateLedger import (
    KSegmentKey,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.VersionTable import (
    VersionAt,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmRecord,
    KAsmToken,
    KAsmValue,
)


def SlotOf(Positions: dict[tuple[KSegmentKey, int], int], KeyValue: KSegmentKey) -> int:
    LastValue = max(Start for ItemValue, Start in Positions if ItemValue == KeyValue)
    return Positions[(KeyValue, LastValue)]


def LifeSlots(
    Contents: list[dict[KSegmentKey, tuple[object, ...]]],
    Positions: dict[tuple[KSegmentKey, int], int],
) -> dict[tuple[KSegmentKey, int], int]:
    Lives: dict[tuple[KSegmentKey, int], int] = {}
    for Index, State in enumerate(Contents):
        for KeyValue in State:
            if (KeyValue, Index) in Lives:
                continue
            Final = Index
            while Final + 1 < len(Contents) and KeyValue in Contents[Final + 1]:
                Final += 1
            Identity = Positions[(KeyValue, VersionAt(Positions, KeyValue, Final))]
            for Within in range(Index, Final + 1):
                Lives[(KeyValue, Within)] = Identity
    return Lives


def AssembleNodes(
    Contents: list[dict[KSegmentKey, tuple[object, ...]]],
    Positions: dict[tuple[KSegmentKey, int], int],
    Order: list[tuple[KSegmentKey, int]],
    Lives: dict[tuple[KSegmentKey, int], int],
) -> tuple[KJournalEntity, ...]:
    Slots = {KeyValue: SlotOf(Positions, KeyValue) for KeyValue, _ in Positions}
    Nodes: list[KJournalEntity] = []
    for KeyValue, Start in Order:
        NameValue, Tokens = Contents[Start][KeyValue]
        if not isinstance(NameValue, str) or not isinstance(Tokens, tuple):
            raise ValueError("Invalid Fusion part journal draft content")
        Pairs = CastValue(tuple[tuple[int, object], ...], Tokens)
        Mapped: tuple[KAsmToken, ...] = tuple(
            (
                TagValue,
                (
                    Lives.get((CastValue(KSegmentKey, Value), Start), Slots[Value])
                    if TagValue == 12 and isinstance(Value, tuple)
                    else CastValue(KAsmValue, Value)
                ),
            )
            for TagValue, Value in Pairs
        )
        Nodes.append(ReadEntityNode(AsmRecord(NameValue, Mapped)))
    return tuple(Nodes)


def StateChanges(
    Contents: list[dict[KSegmentKey, tuple[object, ...]]],
    Positions: dict[tuple[KSegmentKey, int], int],
    Lives: dict[tuple[KSegmentKey, int], int],
    Index: int,
) -> list[tuple[int, int]]:
    After = Contents[Index]
    Before = (
        Contents[Index - 1]
        if Index
        else {
            KeyValue: Value
            for KeyValue, Value in After.items()
            if KeyValue[0] == ("root",)
        }
    )
    Changes: list[tuple[int, int]] = []
    for KeyValue in After:
        Identity = Lives[(KeyValue, Index)]
        if KeyValue not in Before:
            Changes.append((-1, Identity))
        elif Before[KeyValue] != After[KeyValue]:
            OldValue = Positions[(KeyValue, VersionAt(Positions, KeyValue, Index - 1))]
            Changes.append((OldValue, Identity))
    for KeyValue in Before:
        if KeyValue not in After:
            Changes.append(
                (Positions[(KeyValue, VersionAt(Positions, KeyValue, Index - 1))], -1)
            )
    return Changes
