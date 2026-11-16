from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullHard,
    KNullSoft,
    HardOwner,
    HardPointer,
    SoftOwner,
    SoftPointer,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    PlaceMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import (
    CountedSlot,
    ReactorSlot,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Standard.DimensionVars import (
    StyleVars,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderDefaults import (
    KIndexColor,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Standard.TableVocab import (
    KFontFamily,
    KFontFile,
    KLayerSpecs,
    KLinetypeSpecs,
    KStyleSpecs,
    KSwissPitch,
    LayerSpec,
    LinetypeSpec,
)

# white index must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KWhiteIndex = 7

# align all must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KAlignAll = ord("A")

# ambient grey must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KAmbientGrey = 0xC2333333

# dim style must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KDimStyle = "DIMSTYLE:Dim-ISO-25"

# text style must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KTextStyle = "STYLE:Standard"

# the side tables order must stay explicit so native drawing objects use a consistent symbol vocabulary
KSideTables = ("VIEW", "UCS")


# the entry common contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def EntryCommon(ControlKey: str) -> KDraftFields:
    return {
        "ReactorCount": 0,
        "NoXdic": 1,
        "HasDsData": 0,
        "Owner": SoftPointer(ControlKey),
        "Reactors": (),
    }


# the named entry contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def NamedEntry(EntryName: str) -> KDraftFields:
    return {"EntryName": EntryName, "FlagBit": 1, "XrefDependent": 0}


# the control operation needs a consistent construction rule so native drawing objects use a consistent symbol vocabulary
def PlaceControlMut(Ledger: DraftBook, Table: str, Members: KDraftFields) -> str:
    ControlKey = "Control:" + Table
    _ = PlaceMut(
        Ledger,
        ControlKey,
        Table + "_CONTROL",
        {**EntryCommon(ControlKey), "Owner": KNullSoft},
        Members,
    )
    return ControlKey


# the listed members contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def ListedMembers(EntryKeys: tuple[str, ...]) -> KDraftFields:
    return {
        "EntryCount": len(EntryKeys),
        "Entries": tuple(SoftOwner(EntryKey) for EntryKey in EntryKeys),
    }


# the layer operation needs a consistent construction rule so native drawing objects use a consistent symbol vocabulary
def PlaceLayerMut(Ledger: DraftBook, Layer: LayerSpec) -> str:
    KeyText = "LAYER:" + Layer.EntryName
    _ = PlaceMut(
        Ledger,
        KeyText,
        "LAYER",
        EntryCommon("Control:LAYER"),
        {
            **NamedEntry(Layer.EntryName),
            "LayerValues": Layer.LayerValues,
            "ColorIndex": 0,
            "ColorRgb": KIndexColor | KWhiteIndex,
            "ColorFlags": 0,
            "XrefBlock": KNullHard,
            "PlotStyle": HardPointer("NOD/ACAD_PLOTSTYLENAME/Normal"),
            "Material": KNullHard,
            "Linetype": HardPointer("LTYPE:" + Layer.Linetype),
            "Unknown": KNullHard,
        },
    )
    return KeyText


# the dash record contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def DashRecord(Length: float) -> DraftRecord:
    return DraftRecord(
        (
            ("DashLength", Length),
            ("ShapeCode", 0),
            ("OffsetX", 0.0),
            ("OffsetY", 0.0),
            ("Scale", 1.0),
            ("Rotation", 0.0),
            ("ShapeFlag", 0),
        )
    )


# the linetype contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def LinetypeMut(Ledger: DraftBook, Linetype: LinetypeSpec) -> str:
    KeyText = "LTYPE:" + Linetype.EntryName
    Dashes = Linetype.Dashes
    _ = PlaceMut(
        Ledger,
        KeyText,
        "LTYPE",
        EntryCommon("Control:LTYPE"),
        {
            **NamedEntry(Linetype.EntryName),
            "Description": Linetype.Description,
            "PatternLength": Linetype.PatternLength,
            "Alignment": KAlignAll,
            "DashCount": len(Dashes),
            "Dashes": tuple(DashRecord(Stroke) for Stroke in Dashes),
            "XrefBlock": KNullHard,
            "Shapes": tuple(KNullHard for _ in Dashes),
        },
    )
    return KeyText


# the style operation needs a consistent construction rule so native drawing objects use a consistent symbol vocabulary
def PlaceStyleMut(Ledger: DraftBook, EntryName: str, LastHeight: float) -> str:
    KeyText = "STYLE:" + EntryName
    Family = DraftRecord((("1000", KFontFamily), ("1071", KSwissPitch)))
    _ = PlaceMut(
        Ledger,
        KeyText,
        "STYLE",
        EntryCommon("Control:STYLE"),
        {
            **NamedEntry(EntryName),
            "Vertical": 0,
            "ShapeFile": 0,
            "FixedHeight": 0.0,
            "WidthFactor": 1.0,
            "Oblique": 0.0,
            "Generation": 0,
            "LastHeight": LastHeight,
            "FontName": KFontFile,
            "BigFont": "",
            "XrefBlock": KNullHard,
        },
        (DraftEed(HardPointer("APPID:ACAD"), Family),),
    )
    return KeyText


# the dim style contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def DimStyleMut(Ledger: DraftBook) -> str:
    Common = EntryCommon("Control:DIMSTYLE")
    _ = PlaceMut(
        Ledger,
        KDimStyle,
        "DIMSTYLE",
        {**Common, **ReactorSlot(Ledger, KDimStyle)},
        {
            **NamedEntry(KDimStyle.split(":", 1)[1]),
            **StyleVars(),
            "XrefBlock": KNullHard,
            "DimTextStyle": HardPointer(KTextStyle),
        },
    )
    return KDimStyle


# the view fields contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def ViewFields(Paper: PaperSize) -> KDraftFields:
    return {
        "ViewHeight": Paper.PaperHeight,
        "ViewWidth": Paper.PaperWidth,
        "ViewCenter": (Paper.PaperWidth / 2, Paper.PaperHeight / 2),
        "ViewTarget": (0.0, 0.0, 0.0),
        "ViewDirection": (0.0, 0.0, 1.0),
        "TwistAngle": 0.0,
        "LensLength": 50.0,
        "FrontClip": 0.0,
        "BackClip": 0.0,
        "ViewModeFirst": 0,
        "ViewModeSecond": 0,
        "ViewModeThird": 0,
        "ViewModeFourth": 1,
        "RenderMode": 0,
        "DefaultLights": 1,
        "LightingType": 1,
        "Brightness": 0.0,
        "Contrast": 0.0,
        "AmbientIndex": 0,
        "AmbientRgb": KAmbientGrey,
        "AmbientFlags": 0,
    }


# the grid fields contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def GridFields() -> KDraftFields:
    return {
        "LowerLeft": (0.0, 0.0),
        "UpperRight": (1.0, 1.0),
        "UcsFollow": 0,
        "CircleZoom": 1000,
        "FastZoom": 1,
        "UcsIcon": 3,
        "GridOn": 1,
        "GridSpacing": (10.0, 10.0),
        "SnapOn": 0,
        "SnapStyle": 0,
        "SnapIsoPair": 0,
        "SnapAngle": 0.0,
        "SnapBase": (0.0, 0.0),
        "SnapSpacing": (10.0, 10.0),
        "UnknownBit": 0,
        "UcsPerViewport": 1,
        "UcsOrigin": (0.0, 0.0, 0.0),
        "UcsXAxis": (1.0, 0.0, 0.0),
        "UcsYAxis": (0.0, 1.0, 0.0),
        "UcsElevation": 0.0,
        "UcsOrtho": 0,
        "GridFlags": 3,
        "GridMajor": 5,
    }


# the active operation needs a consistent construction rule so native drawing objects use a consistent symbol vocabulary
def PlaceActiveMut(Ledger: DraftBook, Paper: PaperSize) -> str:
    KeyText = "VPORT:*Active"
    Links: dict[str, KDraftValue] = {
        "XrefBlock": KNullHard,
        "Background": KNullSoft,
        "VisualStyle": KNullHard,
        "SunHandle": DwgHandleRef(3, 0),
        "NamedUcs": KNullHard,
        "BaseUcs": KNullHard,
    }
    _ = PlaceMut(
        Ledger,
        KeyText,
        "VPORT",
        EntryCommon("Control:VPORT"),
        {**NamedEntry("*Active"), **ViewFields(Paper), **GridFields(), **Links},
    )
    return KeyText


# the tables operation needs a consistent construction rule so native drawing objects use a consistent symbol vocabulary
def PlaceTablesMut(Ledger: DraftBook, Paper: PaperSize) -> None:
    Linetypes = tuple(LinetypeMut(Ledger, Entry) for Entry in KLinetypeSpecs)
    Layers = tuple(PlaceLayerMut(Ledger, Entry) for Entry in KLayerSpecs)
    Styles = tuple(PlaceStyleMut(Ledger, *Entry) for Entry in KStyleSpecs)
    DimStyle = DimStyleMut(Ledger)
    Active = PlaceActiveMut(Ledger, Paper)
    _ = PlaceControlMut(Ledger, "LAYER", ListedMembers(Layers))
    _ = PlaceControlMut(Ledger, "STYLE", ListedMembers(Styles))
    _ = PlaceControlMut(
        Ledger,
        "LTYPE",
        {
            **ListedMembers(Linetypes[2:]),
            "ByBlock": HardOwner(Linetypes[0]),
            "ByLayer": HardOwner(Linetypes[1]),
        },
    )
    for Table in KSideTables:
        _ = PlaceControlMut(Ledger, Table, ListedMembers(()))
    _ = PlaceControlMut(Ledger, "VPORT", ListedMembers((Active,)))
    _ = PlaceControlMut(
        Ledger,
        "DIMSTYLE",
        {
            **ListedMembers((DimStyle,)),
            "HardCount": 1,
            "HardOwned": (HardPointer(DimStyle),),
        },
    )
    _ = PlaceControlMut(
        Ledger,
        "APPID",
        CountedSlot(Ledger, "Control:APPID.Entries", "EntryCount", "Entries"),
    )
