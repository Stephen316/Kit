from collections.abc import Mapping

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed, DraftRow
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Standard.ReadDefaults import (
    SheetDefaults,
)

# the draft fields shape must stay shared so native drawing authoring uses one contract for compatible values
KDraftFields = Mapping[str, KDraftValue]

# the no defaults order must stay explicit so drawing objects retain valid ownership and reference relationships
KNoDefaults = (DraftRecord(()), DraftRecord(()))


# the merge fields contract needs a stable decomposition so drawing objects retain valid ownership and reference relationships
def MergeFields(Defaults: DraftRecord, Values: KDraftFields) -> DraftRecord:
    Merged = dict(Defaults.DraftFields)
    Merged.update(Values)
    return DraftRecord(tuple(Merged.items()))


# the spare names contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def SpareNames(Defaults: DraftRecord, Values: KDraftFields) -> frozenset[str]:
    return frozenset(
        Called for Called, _ in Defaults.DraftFields if Called not in Values
    )


# the place contract needs a consistent construction rule so drawing objects retain valid ownership and reference relationships
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


# append needs an explicit validity boundary so drawing objects retain valid ownership and reference relationships
def AppendMut(Ledger: DraftBook, SlotName: str, *SlotValues: KDraftValue) -> None:
    if SlotName not in Ledger.SlotItems:
        raise ValueError(f"Authored DWG slot {SlotName!r} is not declared")
    Ledger.SlotItems[SlotName].extend(SlotValues)
