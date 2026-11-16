from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftSlot,
    KDraftValue,
    KSlotBytes,
    KSlotCount,
    KSlotItems,
)


# declare needs an explicit validity boundary so drawing objects retain valid ownership and reference relationships
def DeclareMut(Ledger: DraftBook, SlotName: str) -> str:
    if SlotName in Ledger.SlotItems:
        raise ValueError(f"Authored DWG slot {SlotName!r} is declared twice")
    Ledger.SlotItems[SlotName] = []
    return SlotName


# the counted slot contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def CountedSlot(
    Ledger: DraftBook, SlotName: str, CountName: str, ItemsName: str
) -> dict[str, KDraftValue]:
    _ = DeclareMut(Ledger, SlotName)
    return {
        CountName: DraftSlot(SlotName, KSlotCount),
        ItemsName: DraftSlot(SlotName, KSlotItems),
    }


# the reactor slot contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def ReactorSlot(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    return CountedSlot(Ledger, KeyText + ".Reactors", "ReactorCount", "Reactors")


# the insert slot contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def InsertSlot(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    SlotName = DeclareMut(Ledger, KeyText + ".Inserts")
    return {
        "InsertCounts": DraftSlot(SlotName, KSlotBytes),
        "Inserts": DraftSlot(SlotName, KSlotItems),
    }
