from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftSlot,
    KDraftValue,
    KSlotBytes,
    KSlotCount,
    KSlotItems,
)


def DeclareMut(Ledger: DraftBook, SlotName: str) -> str:
    if SlotName in Ledger.SlotItems:
        raise ValueError(f"Authored DWG slot {SlotName!r} is declared twice")
    Ledger.SlotItems[SlotName] = []
    return SlotName


def CountedSlot(
    Ledger: DraftBook, SlotName: str, CountName: str, ItemsName: str
) -> dict[str, KDraftValue]:
    _ = DeclareMut(Ledger, SlotName)
    return {
        CountName: DraftSlot(SlotName, KSlotCount),
        ItemsName: DraftSlot(SlotName, KSlotItems),
    }


def ReactorSlot(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    return CountedSlot(Ledger, KeyText + ".Reactors", "ReactorCount", "Reactors")


def InsertSlot(Ledger: DraftBook, KeyText: str) -> dict[str, KDraftValue]:
    SlotName = DeclareMut(Ledger, KeyText + ".Inserts")
    return {
        "InsertCounts": DraftSlot(SlotName, KSlotBytes),
        "Inserts": DraftSlot(SlotName, KSlotItems),
    }
