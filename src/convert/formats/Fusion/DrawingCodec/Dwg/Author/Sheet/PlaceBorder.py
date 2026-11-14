from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    HardPointer,
    KNullHard,
    SoftOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import (
    KSegment,
    BorderPlan,
    ZoneLabel,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import OwnMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KBlockEntries,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import (
    CountedSlot,
    InsertSlot,
)

KByLayer = 256
KLayerWeight = 29
KMiddleAlign = 4
KMiddleFlags = 0xBD
KMillimetreUnits = 4
KBorderLayer = "LAYER:BORDER"
KTrimLayer = "LAYER:Defpoints"
KZoneStyle = "STYLE:FusionTitle"


def EntityCommon(BlockKey: str, Layer: str) -> KDraftFields:
    return {
        "EntityMode": 0,
        "Owner": SoftPointer(BlockKey),
        "ColorIndex": KByLayer,
        "LtypeScale": 1.0,
        "LtypeFlags": 0,
        "LineWeight": KLayerWeight,
        "Layer": HardPointer(Layer),
    }


def PlaceSegmentMut(
    Ledger: DraftBook, BlockKey: str, KeyText: str, Layer: str, Segment: KSegment
) -> None:
    (StartX, StartY), (FinishX, FinishY) = Segment
    Points = {"StartX": StartX, "EndX": FinishX, "StartY": StartY, "EndY": FinishY}
    Plane = {"ZeroDepth": 1, "UnitExtrusion": 1, "Thickness": 0.0}
    _ = OwnMut(Ledger, BlockKey, KeyText)
    _ = PlaceMut(
        Ledger, KeyText, "LINE", EntityCommon(BlockKey, Layer), {**Points, **Plane}
    )


def PlaceLabelMut(
    Ledger: DraftBook, BlockKey: str, KeyText: str, Label: ZoneLabel
) -> None:
    _ = OwnMut(Ledger, BlockKey, KeyText)
    _ = PlaceMut(
        Ledger,
        KeyText,
        "TEXT",
        EntityCommon(BlockKey, KBorderLayer),
        {
            "DataFlags": KMiddleFlags,
            "Insertion": Label.Insertion,
            "Alignment": Label.Centre,
            "Extrusion": (0.0, 0.0, 1.0),
            "Thickness": 0.0,
            "Height": Label.TextHeight,
            "TextValue": Label.TextValue,
            "HorizAlign": KMiddleAlign,
            "Style": HardPointer(KZoneStyle),
        },
    )


def SheetBlockMut(Ledger: DraftBook, BlockName: str) -> str:
    BlockKey = "BLOCK_HEADER:" + BlockName
    FolderKey = BlockKey + "/Xdic"
    _ = PlaceMut(
        Ledger,
        BlockKey,
        "BLOCK_HEADER",
        {"NoXdic": 0, "Xdic": HardOwner(FolderKey)},
        {
            "EntryName": BlockName,
            "Anonymous": 0,
            **CountedSlot(Ledger, BlockKey + ".Owned", "OwnedCount", "Owned"),
            **InsertSlot(Ledger, BlockKey),
            "InsertUnits": KMillimetreUnits,
            "BlockEntity": HardOwner(BlockKey + "/BLOCK"),
            "EndBlock": HardOwner(BlockKey + "/ENDBLK"),
            "Layout": KNullHard,
        },
    )
    _ = PlaceMut(
        Ledger,
        FolderKey,
        "DICTIONARY",
        {"ReactorCount": 0, "Owner": SoftPointer(BlockKey), "Reactors": ()},
        {"ItemCount": 0, "HardOwner": 1, "Entries": (), "Items": ()},
    )
    Owner: KDraftFields = {"EntityMode": 0, "Owner": SoftPointer(BlockKey)}
    _ = PlaceMut(Ledger, BlockKey + "/BLOCK", "BLOCK", Owner, {"BlockName": BlockName})
    _ = PlaceMut(Ledger, BlockKey + "/ENDBLK", "ENDBLK", Owner, {})
    AppendMut(Ledger, KBlockEntries, SoftOwner(BlockKey))
    return BlockKey


def PlaceBorderMut(Ledger: DraftBook, Border: BorderPlan) -> str:
    BlockKey = SheetBlockMut(Ledger, Border.BlockName)
    Lines = (
        *((KBorderLayer, Segment) for Segment in Border.FrameLines),
        *((KTrimLayer, Segment) for Segment in Border.TrimLines),
        *((KBorderLayer, Segment) for Segment in Border.MarkLines),
    )
    for Index, (Layer, Segment) in enumerate(Lines):
        PlaceSegmentMut(Ledger, BlockKey, f"{BlockKey}/Line{Index}", Layer, Segment)
    for Index, Label in enumerate(Border.Labels):
        PlaceLabelMut(Ledger, BlockKey, f"{BlockKey}/Zone{Index}", Label)
    return BlockKey
