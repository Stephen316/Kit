from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    SoftOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut


def EntryName(NameText: str) -> DraftRecord:
    return DraftRecord((("EntryName", NameText),))


def PlaceFolderMut(
    Ledger: DraftBook, KeyText: str, OwnerKey: str, IsExtension: bool, NameText: str
) -> str:
    Reactors = () if IsExtension else (SoftPointer(OwnerKey),)
    _ = PlaceMut(
        Ledger,
        KeyText,
        "DICTIONARY",
        {
            "ReactorCount": len(Reactors),
            "Owner": SoftPointer(OwnerKey),
            "Reactors": Reactors,
        },
        {
            "ItemCount": 1,
            "HardOwner": 1 if IsExtension else 0,
            "Entries": (EntryName(NameText),),
            "Items": (SoftOwner(KeyText + "/" + NameText),),
        },
    )
    return KeyText + "/" + NameText


def EntryText(Entry: KDraftValue) -> str:
    if not isinstance(Entry, DraftRecord):
        raise ValueError("Authored DWG dictionary entry is not a named record")
    Value = dict(Entry.DraftFields).get("EntryName")
    if not isinstance(Value, str):
        raise ValueError("Authored DWG dictionary entry has no name")
    return Value


def EnrolMut(Ledger: DraftBook, FolderKey: str, NameText: str, KeyText: str) -> str:
    Names = Ledger.SlotItems.get(FolderKey + ".Entries")
    Items = Ledger.SlotItems.get(FolderKey + ".Items")
    if Names is None or Items is None or len(Names) != len(Items):
        raise ValueError(f"Authored DWG folder {FolderKey!r} takes no entries")
    Folded = NameText.lower()
    Position = sum(1 for Entry in Names if EntryText(Entry).lower() < Folded)
    Names.insert(Position, EntryName(NameText))
    Items.insert(Position, SoftOwner(KeyText))
    return KeyText
