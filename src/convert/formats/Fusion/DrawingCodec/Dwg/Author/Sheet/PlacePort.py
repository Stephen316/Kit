from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HandleNumber,
    HardOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import OwnMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    PlaceFolderMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceRecord import (
    PlaceRecordMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceScale import (
    PlaceScaleMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KLayoutViewports,
    KOverallPort,
    KPaperSpace,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)

KAlwaysOn = 0x8000
KGridBeyond = 0x40000
KAdaptiveGrid = 0x80000
KOverallFlags = KAlwaysOn | KGridBeyond | KAdaptiveGrid
KScaleRecord = "ASDK_XREC_ANNOTATION_SCALE_INFO"


def PlacePortMut(
    Ledger: DraftBook,
    KeyText: str,
    CommonData: Mapping[str, KDraftValue],
    ClassData: Mapping[str, KDraftValue],
    EedBlocks: tuple[DraftEed, ...] = (),
) -> str:
    _ = PlaceMut(Ledger, KeyText, "VIEWPORT", CommonData, ClassData, EedBlocks)
    AppendMut(Ledger, KLayoutViewports, SoftPointer(KeyText))
    return OwnMut(Ledger, KPaperSpace, KeyText)


def PlaceOverallMut(Ledger: DraftBook, Paper: PaperSize) -> str:
    Center = (Paper.PaperWidth / 2, Paper.PaperHeight / 2)
    FolderKey = KOverallPort + "/Xdic"
    _ = PlacePortMut(
        Ledger,
        KOverallPort,
        {
            "ReactorCount": 0,
            "NoXdic": 0,
            "Invisible": 0,
            "Reactors": (),
            "Xdic": HardOwner(FolderKey),
        },
        {
            "Center": (*Center, 0.0),
            "Width": Paper.PaperWidth,
            "Height": Paper.PaperHeight,
            "ViewTarget": (0.0, 0.0, 0.0),
            "ViewDirection": (0.0, 0.0, 1.0),
            "TwistAngle": 0.0,
            "ViewHeight": Paper.PaperHeight,
            "ViewCenter": Center,
            "StatusFlags": KOverallFlags,
            "UcsAtOrigin": 0,
            "UcsOrigin": (0.0, 0.0, 0.0),
            "UcsXAxis": (1.0, 0.0, 0.0),
            "UcsYAxis": (0.0, 1.0, 0.0),
        },
    )
    RecordKey = PlaceFolderMut(Ledger, FolderKey, KOverallPort, True, KScaleRecord)
    ScaleKey = PlaceScaleMut(Ledger, 1.0)
    return PlaceRecordMut(
        Ledger, RecordKey, FolderKey, (("90", 1), ("340", HandleNumber(ScaleKey)))
    )
