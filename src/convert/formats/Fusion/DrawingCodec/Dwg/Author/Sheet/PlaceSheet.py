from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    EnrolMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceNetwork import (
    PlaceNetworkMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlacePort import (
    PlaceOverallMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceTitle import (
    PlaceTitleMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KFirstSheetTab,
    KLayoutFolder,
    KLayoutKey,
    KLayoutViewports,
    KOverallPort,
    KPaperOwned,
    KPaperSpace,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
    SheetSize,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import CountedSlot
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import (
    SheetDraft,
)


def LayoutEed() -> tuple[DraftEed, ...]:
    return (
        DraftEed(
            HardPointer("APPID:FUSIONCURRENTTITLEBLOCK"),
            DraftRecord((("1000", "ISO_TITLEBLOCK"),)),
        ),
    )


def PlacePaperMut(Ledger: DraftBook) -> None:
    _ = PlaceMut(
        Ledger,
        KPaperSpace,
        "BLOCK_HEADER",
        {"NoXdic": 0, "Xdic": HardOwner(KPaperSpace + "/Xdic")},
        {
            "EntryName": "*Paper_Space",
            "Anonymous": 0,
            **CountedSlot(Ledger, KPaperOwned, "OwnedCount", "Owned"),
            "InsertCounts": b"",
            "Inserts": (),
            "BlockEntity": HardOwner(KPaperSpace + "/BLOCK"),
            "EndBlock": HardOwner(KPaperSpace + "/ENDBLK"),
            "Layout": HardPointer(KLayoutKey),
        },
    )
    Modes = {"EntityMode": 1}
    _ = PlaceMut(
        Ledger, KPaperSpace + "/BLOCK", "BLOCK", Modes, {"BlockName": "*Paper_Space"}
    )
    _ = PlaceMut(Ledger, KPaperSpace + "/ENDBLK", "ENDBLK", Modes, {})


def PlaceLayoutMut(Ledger: DraftBook, LayoutName: str, Paper: PaperSize) -> None:
    _ = PlaceMut(
        Ledger,
        KLayoutKey,
        "LAYOUT",
        {},
        {
            "LayoutName": LayoutName,
            "TabOrder": KFirstSheetTab,
            "PaperWidth": Paper.PaperWidth,
            "PaperHeight": Paper.PaperHeight,
            "PaperSize": Paper.MediaName,
            "PaperUnits": 1 if Paper.IsMetric else 0,
            "WindowMin": (0.0, 0.0),
            "WindowMax": (0.0, 0.0),
            "LimitMin": (0.0, 0.0),
            "LimitMax": (Paper.PaperWidth, Paper.PaperHeight),
            "ExtentMin": (0.0, 0.0, 0.0),
            "ExtentMax": (Paper.PaperWidth, Paper.PaperHeight, 0.0),
            "BlockRecord": SoftPointer(KPaperSpace),
            "LastViewport": SoftPointer(KOverallPort),
            **CountedSlot(Ledger, KLayoutViewports, "ViewportCount", "Viewports"),
        },
        LayoutEed(),
    )
    _ = EnrolMut(Ledger, KLayoutFolder, LayoutName, KLayoutKey)


def PlaceSheetMut(Ledger: DraftBook, Draft: SheetDraft) -> None:
    Paper = SheetSize(Draft.SheetSize)
    PlacePaperMut(Ledger)
    PlaceLayoutMut(Ledger, Draft.LayoutName, Paper)
    PlaceNetworkMut(Ledger)
    _ = PlaceOverallMut(Ledger, Paper)
    PlaceTitleMut(Ledger, Paper, Draft.TitleTexts)
