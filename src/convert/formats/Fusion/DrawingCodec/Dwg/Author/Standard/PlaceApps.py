from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullHard,
    SoftOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)

KAppPrefix = "APPID:"
KAppEntries = "Control:APPID.Entries"
KFirstApp = KAppPrefix + "ACAD"


def UsedApps(Ledger: DraftBook) -> tuple[str, ...]:
    Found = [KFirstApp]
    for Entry in Ledger.DraftRows:
        for Block in Entry.EedBlocks:
            KeyText = Block.AppLink.KeyText
            if KeyText.startswith(KAppPrefix) and KeyText not in Found:
                Found.append(KeyText)
    return tuple(Found)


def PlaceAppsMut(Ledger: DraftBook) -> None:
    for KeyText in UsedApps(Ledger):
        _ = PlaceMut(
            Ledger,
            KeyText,
            "APPID",
            {
                "ReactorCount": 0,
                "NoXdic": 1,
                "HasDsData": 0,
                "Owner": SoftPointer("Control:APPID"),
                "Reactors": (),
            },
            {
                "EntryName": KeyText.removeprefix(KAppPrefix),
                "FlagBit": 1,
                "XrefDependent": 0,
                "Unknown": 0,
                "XrefBlock": KNullHard,
            },
        )
        AppendMut(Ledger, KAppEntries, SoftOwner(KeyText))
