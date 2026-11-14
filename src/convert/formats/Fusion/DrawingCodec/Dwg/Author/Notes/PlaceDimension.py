from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from math import cos as Cosine
from math import sin as SineOf

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KTextHeight,
    DimensionPlan,
    PlanDimension,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import (
    OwnMut,
    PlaceBlockMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import KPaperSpace
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)

KStyleKey = "DIMSTYLE:Dim-ISO-25"
KDimLayer = "LAYER:FD_Dimensions"
KPointLayer = "LAYER:Defpoints"
KByBlock = 8192
KLineWeight = 30
KJagGroups = (("1070", 387), ("1070", 0), ("1070", 389), ("1010", (0.0, 0.0, 0.0)))
KSuppressFirst = 75
KUserPlaced = 288
KStyleOverrides: dict[str, tuple[int, ...]] = {
    "Radius": (KSuppressFirst, KUserPlaced),
    "Diameter": (KUserPlaced,),
}
KPlacedText = 10
KDraftFields = dict[str, KDraftValue]
KClassNames = {
    "Horizontal": "DIMENSION_LINEAR",
    "Vertical": "DIMENSION_LINEAR",
    "Aligned": "DIMENSION_ALIGNED",
    "Radius": "DIMENSION_RADIUS",
    "Diameter": "DIMENSION_DIAMETER",
}


def FactorItem(NameText: str, Value: float) -> DraftEed:
    return DraftEed(HardPointer("APPID:" + NameText), DraftRecord((("1040", Value),)))


def FactorEed(Factor: float, DimensionKind: str) -> tuple[DraftEed, ...]:
    Overrides: tuple[tuple[str, KDraftValue], ...] = tuple(
        Override
        for Variable in KStyleOverrides.get(DimensionKind, ())
        for Override in (("1070", Variable), ("1070", 1))
    )
    Style: tuple[tuple[str, KDraftValue], ...] = (
        ("1000", "DSTYLE"),
        ("1002", 0),
        ("1070", 144),
        ("1040", Factor),
        *Overrides,
        ("1002", 1),
    )
    return (
        DraftEed(HardPointer("APPID:ACAD"), DraftRecord(Style)),
        FactorItem("ACAD_DIMASSOC_CALC_DIMLFAC", Factor),
        FactorItem("ACAD_DIMASSOC_DIMLFAC", Factor),
        FactorItem("ACAD_DIMASSOC_OVERRIDDEN_DIMLFAC", 0.0),
        DraftEed(
            HardPointer("APPID:ACAD_DSTYLE_DIMJAG_POSITION"), DraftRecord(KJagGroups)
        ),
    )


def BlockCommon(BlockKey: str, Layer: str) -> KDraftFields:
    return {
        "EntityMode": 0,
        "Owner": SoftPointer(BlockKey),
        "ColorIndex": KByBlock,
        "LtypeScale": 1.0,
        "LtypeFlags": 0,
        "Layer": HardPointer(Layer),
    }


def PlaceLinesMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    for Index, (Start, Finish) in enumerate(Planned.Lines):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Line{Index}")
        Common = {**BlockCommon(BlockKey, KDimLayer), "LineWeight": KLineWeight}
        Points = {
            "StartX": Start[0],
            "EndX": Finish[0],
            "StartY": Start[1],
            "EndY": Finish[1],
        }
        Plane = {"ZeroDepth": 1, "UnitExtrusion": 1, "Thickness": 0.0}
        _ = PlaceMut(Ledger, KeyText, "LINE", Common, {**Points, **Plane})
    for Index, (Corner, Second, Apical) in enumerate(Planned.Arrows):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Arrow{Index}")
        Corners = {
            "CornerOne": Corner,
            "CornerTwo": Second,
            "CornerThree": Apical,
            "CornerFour": Apical,
        }
        _ = PlaceMut(
            Ledger, KeyText, "SOLID", BlockCommon(BlockKey, KDimLayer), Corners
        )


def PlaceTextMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Text")
    Point = (*Planned.TextPoint, 0.0)
    Width = Planned.TextWidth
    Across = (Cosine(Planned.TextAngle), SineOf(Planned.TextAngle), 0.0)
    _ = PlaceMut(
        Ledger,
        KeyText,
        "MTEXT",
        BlockCommon(BlockKey, KDimLayer),
        {
            "Insertion": Point,
            "XAxis": Across,
            "RectWidth": 0.0,
            "RectHeight": 0.0,
            "TextHeight": KTextHeight,
            "ExtentHeight": Planned.TextHeight,
            "ExtentWidth": Width,
            "TextValue": Planned.TextValue,
            "ContextXAxis": Across,
            "ContextInsertion": Point,
            "ContextWidth": 0.0,
            "ContextHeight": 0.0,
            "ContextExtWidth": Width,
            "ContextExtHeight": Planned.TextHeight,
        },
    )


def PlacePointsMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    for Index, Point in enumerate(Planned.Anchors):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Point{Index}")
        Place = {"PointX": Point[0], "PointY": Point[1], "PointZ": 0.0}
        _ = PlaceMut(
            Ledger, KeyText, "POINT", BlockCommon(BlockKey, KPointLayer), Place
        )


def KindFields(Planned: DimensionPlan) -> KDraftFields:
    First = (*Planned.FirstPoint, 0.0)
    Second = (*Planned.SecondPoint, 0.0)
    if Planned.DimensionKind in ("Radius", "Diameter"):
        Leader = 0.0
        return {
            "PointTen": First,
            "PointFifteen": Second,
            "LeaderLength": Leader,
            "DimFlags": KPlacedText,
        }
    Fields: KDraftFields = {
        "PointThirteen": First,
        "PointFourteen": Second,
        "PointTen": (*Planned.LinePoint, 0.0),
        "ExtRotation": 0.0,
    }
    if Planned.DimensionKind != "Aligned":
        Fields["DimRotation"] = Planned.LineAngle
    return Fields


def PlaceDimMut(Ledger: DraftBook, Index: int, Draft: DimensionDraft) -> str:
    Planned = PlanDimension(Draft)
    BlockKey = PlaceBlockMut(Ledger, f"BLOCK_HEADER:Dimension{Index}", "*D")
    PlaceLinesMut(Ledger, BlockKey, Planned)
    PlaceTextMut(Ledger, BlockKey, Planned)
    PlacePointsMut(Ledger, BlockKey, Planned)
    KeyText = OwnMut(Ledger, KPaperSpace, f"{KPaperSpace}/Dimension{Index}")
    _ = PlaceMut(
        Ledger,
        KeyText,
        KClassNames[Planned.DimensionKind],
        {"ReactorCount": 0, "Reactors": ()},
        {
            "TextMidpoint": Planned.TextPoint,
            "Measurement": Planned.Measurement,
            "DimStyle": HardPointer(KStyleKey),
            "DimBlock": HardPointer(BlockKey),
            **KindFields(Planned),
        },
        FactorEed(Planned.LinearFactor, Planned.DimensionKind),
    )
    AppendMut(Ledger, KStyleKey + ".Reactors", SoftPointer(KeyText))
    return KeyText
