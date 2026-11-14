from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed, DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDefaults import (
    SheetDefaults,
)

KDraftFields = Mapping[str, KDraftValue]
KNoDefaults = (DraftRecord(()), DraftRecord(()))


def MergeFields(Defaults: DraftRecord, Values: KDraftFields) -> DraftRecord:
    Merged = dict(Defaults.DraftFields)
    Merged.update(Values)
    return DraftRecord(tuple(Merged.items()))


def SpareNames(Defaults: DraftRecord, Values: KDraftFields) -> frozenset[str]:
    return frozenset(
        Called for Called, _ in Defaults.DraftFields if Called not in Values
    )


def PlaceMut(
    Ledger: DraftBook,
    KeyText: str,
    ClassName: str,
    CommonData: KDraftFields,
    ClassData: KDraftFields,
    EedBlocks: tuple[DraftEed, ...] = (),
) -> str:
    Defaults = SheetDefaults().get(ClassName, KNoDefaults)
    Entry = DraftRow(
        KeyText,
        ClassName,
        MergeFields(Defaults[0], CommonData),
        MergeFields(Defaults[1], ClassData),
        EedBlocks,
        SpareNames(Defaults[0], CommonData),
        SpareNames(Defaults[1], ClassData),
    )
    Ledger.DraftRows.append(Entry)
    return KeyText


def AppendMut(Ledger: DraftBook, SlotName: str, *SlotValues: KDraftValue) -> None:
    if SlotName not in Ledger.SlotItems:
        raise ValueError(f"Authored DWG slot {SlotName!r} is not declared")
    Ledger.SlotItems[SlotName].extend(SlotValues)
