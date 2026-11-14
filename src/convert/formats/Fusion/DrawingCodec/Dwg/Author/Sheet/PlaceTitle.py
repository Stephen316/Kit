from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import PlanBorder
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import OwnMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBorder import (
    EntityCommon,
    PlaceBorderMut,
    PlaceSegmentMut,
    SheetBlockMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KPaperSpace,
    KTitleBlock,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.TitlePlan import (
    KLabelHeight,
    PlanTitle,
    TitlePlan,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText

KWidthDefault = 0x10
KTopLeftFlags = 0x7D
KTopAlign = 3
KTitleLayer = "LAYER:TITLEBLOCK"
KTitleStyle = "STYLE:FusionTitle"
KAttdefCommon: dict[str, KDraftValue] = {
    "HasGraphics": 0,
    "EntityMode": 0,
    "ReactorCount": 0,
    "NoXdic": 1,
    "HasDsData": 0,
    "ColorIndex": 256,
    "LtypeScale": 1.0,
    "LtypeFlags": 0,
    "MaterialFlags": 0,
    "PlotFlags": 0,
    "ShadowFlags": 0,
    "HasFullStyle": 0,
    "HasFaceStyle": 0,
    "HasEdgeStyle": 0,
    "Invisible": 0,
    "LineWeight": 29,
}
KDefinitionOnly = ("DefVersion", "Prompt")
KTitleInsert = KPaperSpace + "/Title"
KBorderInsert = KPaperSpace + "/Border"
KPoint = tuple[float, float]


def TopLeftData(Corner: KPoint, Height: float) -> dict[str, KDraftValue]:
    return {
        "DataFlags": KTopLeftFlags,
        "Insertion": (Corner[0], Corner[1] - Height),
        "Alignment": Corner,
        "Extrusion": (0.0, 0.0, 1.0),
        "Thickness": 0.0,
        "Height": Height,
        "VertAlign": KTopAlign,
        "Style": HardPointer(KTitleStyle),
    }


def AttdefCommon(BlockKey: str) -> dict[str, KDraftValue]:
    return {
        **KAttdefCommon,
        "Owner": SoftPointer(BlockKey),
        "Reactors": (),
        "Layer": HardPointer(KTitleLayer),
    }


def TitleBlockMut(Ledger: DraftBook, Title: TitlePlan) -> None:
    BlockKey = SheetBlockMut(Ledger, KTitleBlock.split(":", 1)[1])
    for Index, Segment in enumerate(Title.Lines):
        PlaceSegmentMut(
            Ledger, BlockKey, f"{BlockKey}/Line{Index}", KTitleLayer, Segment
        )
    for Index, Field in enumerate(Title.Fields):
        LabelKey = f"{BlockKey}/Label{Index}"
        _ = OwnMut(Ledger, BlockKey, LabelKey)
        _ = PlaceMut(
            Ledger,
            LabelKey,
            "TEXT",
            EntityCommon(BlockKey, KTitleLayer),
            {**TopLeftData(Field.LabelCorner, KLabelHeight), "TextValue": Field.Prompt},
        )
        FieldKey = f"{KTitleBlock}/{Field.Tag}"
        _ = OwnMut(Ledger, BlockKey, FieldKey)
        _ = PlaceMut(
            Ledger,
            FieldKey,
            "ATTDEF",
            AttdefCommon(BlockKey),
            {
                **TopLeftData(Field.ValueCorner, Field.ValueHeight),
                "TextValue": "",
                "AttribVersion": 0,
                "AttribType": 1,
                "Tag": Field.Tag,
                "FieldLength": 0,
                "AttribFlags": 0,
                "LockPosition": 1,
                "DefVersion": 0,
                "Prompt": Field.Prompt,
            },
        )


def PlaceInsertMut(
    Ledger: DraftBook,
    KeyText: str,
    BlockKey: str,
    Corner: KPoint,
    ClassData: Mapping[str, KDraftValue],
) -> None:
    Layer = KTitleLayer if BlockKey == KTitleBlock else "LAYER:BORDER"
    _ = PlaceMut(
        Ledger,
        KeyText,
        "INSERT",
        {
            "ReactorCount": 0,
            "LtypeScale": 1.0,
            "Reactors": (),
            "Layer": HardPointer(Layer),
        },
        {
            "Insertion": (*Corner, 0.0),
            "BlockHeader": HardPointer(BlockKey),
            **ClassData,
        },
    )
    AppendMut(Ledger, BlockKey + ".Inserts", SoftPointer(KeyText))
    _ = OwnMut(Ledger, KPaperSpace, KeyText)


def PlanarPoint(Value: KDraftValue) -> KPoint:
    if not isinstance(Value, tuple) or len(Value) != 2:
        raise ValueError("Authored DWG title attribute has no planar position")
    Across, Upward = Value
    if not isinstance(Across, float) or not isinstance(Upward, float):
        raise ValueError("Authored DWG title attribute position is not numeric")
    return (Across, Upward)


def Shifted(Value: KDraftValue, Corner: KPoint) -> KPoint:
    Across, Upward = PlanarPoint(Value)
    return (Across + Corner[0], Upward + Corner[1])


def AttribData(
    Definition: DraftRow, Chosen: TitleText, Corner: KPoint
) -> dict[str, KDraftValue]:
    Fields = dict(Definition.ClassData.DraftFields)
    for NameText in KDefinitionOnly:
        _ = Fields.pop(NameText)
    Alignment = Shifted(Fields["Alignment"], Corner)
    IsAligned = "HorizAlign" in Fields
    Fields["Alignment"] = Alignment
    Fields["Insertion"] = (
        Alignment if IsAligned else Shifted(Fields["Insertion"], Corner)
    )
    Fields["TextValue"] = Chosen.TextValue
    Flags = Fields["DataFlags"]
    if Chosen.WidthFactor != 1.0 and isinstance(Flags, int):
        Fields["DataFlags"] = Flags & ~KWidthDefault
        Fields["WidthFactor"] = Chosen.WidthFactor
    return Fields


def TagOf(Definition: DraftRow) -> str:
    return str(dict(Definition.ClassData.DraftFields)["Tag"])


def PlaceTitleMut(
    Ledger: DraftBook, Paper: PaperSize, Texts: tuple[TitleText, ...]
) -> None:
    BorderBlock = PlaceBorderMut(Ledger, PlanBorder(Paper))
    TitleBlockMut(Ledger, PlanTitle())
    PlaceInsertMut(Ledger, KBorderInsert, BorderBlock, (0.0, 0.0), {"HasAttribs": 0})
    Definitions = [
        Entry
        for Entry in Ledger.DraftRows
        if Entry.ClassName == "ATTDEF" and Entry.KeyText.startswith(KTitleBlock + "/")
    ]
    Chosen = {Title.Tag: Title for Title in Texts}
    Unknown = set(Chosen) - {TagOf(Entry) for Entry in Definitions}
    if Unknown:
        raise ValueError(
            f"Authored DWG title block has no attributes {sorted(Unknown)}"
        )
    Attribs = tuple(
        f"{KTitleInsert}/Attrib{Index}" for Index in range(len(Definitions))
    )
    TitleData: dict[str, KDraftValue] = {
        "HasAttribs": 1,
        "OwnedCount": len(Attribs),
        "Attribs": tuple(HardOwner(KeyText) for KeyText in Attribs),
        "SeqEnd": HardOwner(KTitleInsert + "/SeqEnd"),
    }
    PlaceInsertMut(Ledger, KTitleInsert, KTitleBlock, Paper.TitleCorner, TitleData)
    Owner = {"Owner": SoftPointer(KTitleInsert)}
    for KeyText, Entry in zip(Attribs, Definitions):
        Title = Chosen.get(TagOf(Entry), TitleText(TagOf(Entry), ""))
        _ = PlaceMut(
            Ledger,
            KeyText,
            "ATTRIB",
            Owner,
            AttribData(Entry, Title, Paper.TitleCorner),
        )
    _ = PlaceMut(
        Ledger, KTitleInsert + "/SeqEnd", "SEQEND", {**Owner, "ShadowFlags": 3}, {}
    )
