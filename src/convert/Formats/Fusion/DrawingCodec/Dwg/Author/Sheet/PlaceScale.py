from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import SoftPointer
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    EnrolMut,
)

# scale folder must remain consistent across callers so paper layouts retain consistent object ownership
KScaleFolder = "NOD/ACAD_SCALELIST"


# the name operation needs one geometric convention so paper layouts retain consistent object ownership
def ScaleName(ViewScale: float) -> str:
    if ViewScale <= 0:
        raise ValueError("Authored DWG view scale must be positive")
    if ViewScale >= 1:
        return f"{ViewScale:g}:1"
    return f"1:{1 / ViewScale:g}"


# the scale operation needs a consistent construction rule so paper layouts retain consistent object ownership
def PlaceScaleMut(Ledger: DraftBook, ViewScale: float) -> str:
    NameText = ScaleName(ViewScale)
    KeyText = KScaleFolder + "/" + NameText
    if any(Entry.KeyText == KeyText for Entry in Ledger.DraftRows):
        return KeyText
    PaperUnits, DrawingUnits = (
        (ViewScale, 1.0) if ViewScale >= 1 else (1.0, 1 / ViewScale)
    )
    _ = PlaceMut(
        Ledger,
        KeyText,
        "SCALE",
        {
            "ReactorCount": 1,
            "NoXdic": 1,
            "HasDsData": 0,
            "Owner": SoftPointer(KScaleFolder),
            "Reactors": (SoftPointer(KScaleFolder),),
        },
        {
            "Unknown": 0,
            "ScaleName": NameText,
            "PaperUnits": PaperUnits,
            "DrawingUnits": DrawingUnits,
            "UnitScale": 1 if ViewScale == 1 else 0,
        },
    )
    EntryText = f"A{len(Ledger.SlotItems[KScaleFolder + '.Items'])}"
    return EnrolMut(Ledger, KScaleFolder, EntryText, KeyText)
