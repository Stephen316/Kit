from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    KNullHard,
    SoftOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KBlockEntries,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import (
    CountedSlot,
    InsertSlot,
)


def BlockSerial(Ledger: DraftBook) -> int:
    return sum(1 for Entry in Ledger.DraftRows if Entry.ClassName == "BLOCK")


def PlaceBlockMut(Ledger: DraftBook, KeyText: str, EntryName: str) -> str:
    BlockName = f"{EntryName}{BlockSerial(Ledger) + 1}"
    _ = PlaceMut(
        Ledger,
        KeyText,
        "BLOCK_HEADER",
        {"NoXdic": 1},
        {
            "EntryName": EntryName,
            "Anonymous": 1,
            **CountedSlot(Ledger, KeyText + ".Owned", "OwnedCount", "Owned"),
            **InsertSlot(Ledger, KeyText),
            "BlockEntity": HardOwner(KeyText + "/BLOCK"),
            "EndBlock": HardOwner(KeyText + "/ENDBLK"),
            "Layout": KNullHard,
        },
    )
    Owner: KDraftFields = {"EntityMode": 0, "Owner": SoftPointer(KeyText)}
    _ = PlaceMut(Ledger, KeyText + "/BLOCK", "BLOCK", Owner, {"BlockName": BlockName})
    _ = PlaceMut(Ledger, KeyText + "/ENDBLK", "ENDBLK", Owner, {})
    AppendMut(Ledger, KBlockEntries, SoftOwner(KeyText))
    return KeyText


def OwnMut(Ledger: DraftBook, BlockKey: str, KeyText: str) -> str:
    AppendMut(Ledger, BlockKey + ".Owned", HardOwner(KeyText))
    return KeyText
