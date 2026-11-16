from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    SoftOwner,
    SoftPointer,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut


# the entry name contract needs a shared interpretation so paper layouts retain consistent object ownership
def EntryName(NameText: str) -> DraftRecord:
    return DraftRecord((("EntryName", NameText),))


# the folder operation needs a consistent construction rule so paper layouts retain consistent object ownership
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


# entry text needs an explicit validity boundary so paper layouts retain consistent object ownership
def EntryText(Entry: KDraftValue) -> str:
    if not isinstance(Entry, DraftRecord):
        raise ValueError("Authored DWG dictionary entry is not a named record")
    Value = dict(Entry.DraftFields).get("EntryName")
    if not isinstance(Value, str):
        raise ValueError("Authored DWG dictionary entry has no name")
    return Value


# enrol needs an explicit validity boundary so paper layouts retain consistent object ownership
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
