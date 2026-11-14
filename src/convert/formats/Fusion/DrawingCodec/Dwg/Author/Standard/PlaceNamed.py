from math import pi as KHalfTurn

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullSoft,
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    DraftSlot,
    KSlotCount,
    KSlotItems,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import EnrolMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KBlockEntries,
    KLayoutFolder,
    KModelOwned,
    KModelSpace,
    KNamedObjects,
    KPaperSpace,
    KRootFolder,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import (
    CountedSlot,
    DeclareMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderDefaults import (
    KByLayerColor,
)

KEmptyFolders = ("ACAD_GROUP", "ACAD_PLOTSETTINGS", "ACAD_COLOR", "ACAD_VISUALSTYLE")
KSlotFolders = ("ACAD_LAYOUT", "ACAD_SCALELIST", "SY_ROOT_DICTIONARY")
KMaterials = ("ByBlock", "ByLayer")
KFileSource = 1
KSceneSource = 0
KAllChannels = 63
KCylinderMap = 2
KTileMap = 1
KViewStandard = (
    ("StandardVersion", 100),
    ("StandardLongOne", 0),
    ("StandardLongTwo", 1),
    ("StandardLongThree", 0),
    ("StandardLongFour", 1),
    ("StandardLongFive", 1),
)


def ChildCommon(OwnerKey: str) -> KDraftFields:
    return {
        "ReactorCount": 1,
        "NoXdic": 1,
        "HasDsData": 0,
        "Owner": SoftPointer(OwnerKey),
        "Reactors": (SoftPointer(OwnerKey),),
    }


def SlotFolder(Ledger: DraftBook, KeyText: str) -> KDraftFields:
    Names = DeclareMut(Ledger, KeyText + ".Entries")
    Items = DeclareMut(Ledger, KeyText + ".Items")
    return {
        "ItemCount": DraftSlot(Items, KSlotCount),
        "Cloning": 1,
        "HardOwner": 0,
        "Entries": DraftSlot(Names, KSlotItems),
        "Items": DraftSlot(Items, KSlotItems),
    }


def PlaceFolderMut(
    Ledger: DraftBook, NameText: str, ClassName: str = "DICTIONARY"
) -> str:
    KeyText = KNamedObjects + "/" + NameText
    Extra: KDraftFields = {}
    if ClassName != "DICTIONARY":
        Extra = {"DefaultEntry": HardPointer(KeyText + "/Normal")}
    _ = PlaceMut(
        Ledger,
        KeyText,
        ClassName,
        ChildCommon(KNamedObjects),
        {**SlotFolder(Ledger, KeyText), **Extra},
    )
    _ = EnrolMut(Ledger, KNamedObjects, NameText, KeyText)
    return KeyText


def MapRecord(Source: int) -> DraftRecord:
    Identity = tuple(
        DraftRecord((("Element", 1.0 if Index % 5 == 0 else 0.0),))
        for Index in range(16)
    )
    Named = (("FileName", ""),) if Source == KFileSource else ()
    return DraftRecord(
        (
            ("BlendFactor", 1.0),
            ("Projection", KCylinderMap),
            ("Tiling", KTileMap),
            ("AutoTransform", 1),
            ("Transform", Identity),
            ("MapSource", Source),
            *Named,
        )
    )


def MaterialData(NameText: str) -> KDraftFields:
    Plain = MapRecord(KFileSource)
    return {
        "MaterialName": NameText,
        "Description": "",
        "AmbientMethod": 0,
        "AmbientFactor": 1.0,
        "DiffuseMethod": 0,
        "DiffuseFactor": 1.0,
        "DiffuseMap": Plain,
        "SpecularMethod": 0,
        "SpecularFactor": 1.0,
        "SpecularMap": Plain,
        "GlossFactor": 0.5,
        "ReflectionMap": Plain,
        "OpacityPercent": 1.0,
        "OpacityMap": Plain,
        "BumpMap": Plain,
        "RefractionIndex": 1.0,
        "RefractionMap": MapRecord(KSceneSource),
        "Translucence": 0.0,
        "SelfIllumination": 0.0,
        "Reflectivity": 0.0,
        "IlluminationModel": 0,
        "ChannelFlags": KAllChannels,
        "MaterialMode": 0,
    }


def LineRecord(Offset: float) -> DraftRecord:
    return DraftRecord(
        (
            ("Offset", Offset),
            ("ColorIndex", 0),
            ("ColorRgb", KByLayerColor),
            ("ColorFlags", 0),
            ("Ltype", HardPointer("LTYPE:ByLayer")),
        )
    )


def PlaceChildMut(
    Ledger: DraftBook,
    FolderKey: str,
    NameText: str,
    ClassName: str,
    ClassData: KDraftFields,
) -> str:
    KeyText = FolderKey + "/" + NameText
    _ = PlaceMut(Ledger, KeyText, ClassName, ChildCommon(FolderKey), ClassData)
    _ = EnrolMut(Ledger, FolderKey, NameText, KeyText)
    return KeyText


def PlaceStylesMut(Ledger: DraftBook) -> None:
    Materials = PlaceFolderMut(Ledger, "ACAD_MATERIAL")
    for NameText in KMaterials:
        _ = PlaceChildMut(
            Ledger, Materials, NameText, "MATERIAL", MaterialData(NameText)
        )
    Lines = PlaceFolderMut(Ledger, "ACAD_MLINESTYLE")
    Standard: KDraftFields = {
        "StyleName": "STANDARD",
        "Description": "",
        "StyleFlags": 0,
        "FillColorIndex": 0,
        "FillColorRgb": KByLayerColor,
        "FillColorFlags": 0,
        "StartAngle": KHalfTurn / 2,
        "EndAngle": KHalfTurn / 2,
        "LineCount": 2,
        "Lines": (LineRecord(0.5), LineRecord(-0.5)),
    }
    _ = PlaceChildMut(Ledger, Lines, "Standard", "MLINESTYLE", Standard)
    Plots = PlaceFolderMut(Ledger, "ACAD_PLOTSTYLENAME", "ACDBDICTIONARYWDFLT")
    _ = PlaceChildMut(Ledger, Plots, "Normal", "ACDBPLACEHOLDER", {})


def PlaceModelMut(Ledger: DraftBook, Paper: PaperSize) -> None:
    ModelLayout = KLayoutFolder + "/Model"
    _ = PlaceMut(
        Ledger,
        KModelSpace,
        "BLOCK_HEADER",
        {"NoXdic": 1},
        {
            "EntryName": "*Model_Space",
            "Anonymous": 0,
            **CountedSlot(Ledger, KModelOwned, "OwnedCount", "Owned"),
            "InsertCounts": b"",
            "Inserts": (),
            "BlockEntity": HardOwner(KModelSpace + "/BLOCK"),
            "EndBlock": HardOwner(KModelSpace + "/ENDBLK"),
            "Layout": HardPointer(ModelLayout),
        },
    )
    Modes = {"EntityMode": 2}
    _ = PlaceMut(
        Ledger, KModelSpace + "/BLOCK", "BLOCK", Modes, {"BlockName": "*Model_Space"}
    )
    _ = PlaceMut(Ledger, KModelSpace + "/ENDBLK", "ENDBLK", Modes, {})
    _ = PlaceMut(
        Ledger,
        ModelLayout,
        "LAYOUT",
        {},
        {
            "LayoutName": "Model",
            "PaperWidth": Paper.PaperWidth,
            "PaperHeight": Paper.PaperHeight,
            "PaperSize": Paper.MediaName,
            "PaperUnits": 1 if Paper.IsMetric else 0,
            "WindowMin": (0.0, 0.0),
            "WindowMax": (0.0, 0.0),
            "TabOrder": 0,
            "LayoutFlags": 1,
            "LimitMin": (0.0, 0.0),
            "LimitMax": (Paper.PaperWidth, Paper.PaperHeight),
            "ExtentMin": (0.0, 0.0, 0.0),
            "ExtentMax": (0.0, 0.0, 0.0),
            "BlockRecord": SoftPointer(KModelSpace),
            "LastViewport": SoftPointer("VPORT:*Active"),
            "ViewportCount": 0,
            "Viewports": (),
        },
    )
    _ = EnrolMut(Ledger, KLayoutFolder, "Model", ModelLayout)


def PlaceNamedMut(Ledger: DraftBook, Paper: PaperSize) -> None:
    _ = PlaceMut(
        Ledger,
        KNamedObjects,
        "DICTIONARY",
        {"ReactorCount": 0, "Owner": KNullSoft, "Reactors": ()},
        SlotFolder(Ledger, KNamedObjects),
    )
    for NameText in KEmptyFolders:
        _ = PlaceFolderMut(Ledger, NameText)
    for NameText in KSlotFolders:
        _ = PlaceFolderMut(Ledger, NameText)
    PlaceStylesMut(Ledger)
    _ = PlaceChildMut(
        Ledger, KRootFolder, "SY_VIEWSTD", "ACDBVIEWREPSTANDARD", dict(KViewStandard)
    )
    PlaceModelMut(Ledger, Paper)
    _ = PlaceMut(
        Ledger,
        "Control:BLOCK",
        "BLOCK_CONTROL",
        {
            "ReactorCount": 0,
            "NoXdic": 1,
            "HasDsData": 0,
            "Owner": KNullSoft,
            "Reactors": (),
        },
        {
            **CountedSlot(Ledger, KBlockEntries, "EntryCount", "Entries"),
            "ModelSpace": HardOwner(KModelSpace),
            "PaperSpace": HardOwner(KPaperSpace),
        },
    )
