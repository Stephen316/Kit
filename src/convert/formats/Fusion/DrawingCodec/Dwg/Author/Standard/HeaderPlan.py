from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullHard,
    HardOwner,
    HardPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KTextHeight,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.DimensionVars import (
    DimensionVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Standard.HeaderDefaults import (
    KCountVars,
    KInterfereVars,
    KLegacyHead,
    KModernVars,
    KRealVars,
    KStampVars,
    KSurfaceVars,
    KSwitchVars,
    KVarGroup,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

# text style must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KTextStyle = "STYLE:Standard"

# dim style must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KDimStyle = "DIMSTYLE:Dim-ISO-25"

# the point shape must stay shared so drawing standard authoring uses one contract for compatible values
KPoint = tuple[float, float, float]

# empty far must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KEmptyFar = 1e20

# the empty box order must stay explicit so native drawing objects use a consistent symbol vocabulary
KEmptyBox = ((KEmptyFar, KEmptyFar, KEmptyFar), (-KEmptyFar, -KEmptyFar, -KEmptyFar))

# zero guid must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KZeroGuid = "{00000000-0000-0000-0000-000000000000}"

# layer weight must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KLayerWeight = 29

# plain lines must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KPlainLines = 0x200

# long names must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KLongNames = 0x800

# named plots must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KNamedPlots = 0x2000

# millimetre units must remain consistent across callers so native drawing objects use a consistent symbol vocabulary
KMillimetreUnits = 4

# the ucs corners order must stay explicit so native drawing objects use a consistent symbol vocabulary
KUcsCorners = ("Top", "Bottom", "Left", "Right", "Front", "Back")

# the table owners order must stay explicit so native drawing objects use a consistent symbol vocabulary
KTableOwners = ("BLOCK", "LAYER", "STYLE", "LTYPE", "VIEW", "UCS", "VPORT")

# the dictionaries order must stay explicit so native drawing objects use a consistent symbol vocabulary
KDictionaries = (
    ("LayoutDictHandle", "LAYOUT"),
    ("PlotSettingsDictHandle", "PLOTSETTINGS"),
    ("PlotStyleDictHandle", "PLOTSTYLENAME"),
    ("MaterialDictHandle", "MATERIAL"),
    ("ColorDictHandle", "COLOR"),
    ("VisualStyleDictHandle", "VISUALSTYLE"),
)


# the current vars contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def CurrentVars() -> KVarGroup:
    return {
        "HandSeed": DwgHandleRef(0, 0),
        "ClayerHandle": HardPointer("LAYER:0"),
        "TextStyleHandle": HardPointer(KTextStyle),
        "CeltypeHandle": HardPointer("LTYPE:ByLayer"),
        "CmaterialHandle": HardPointer("NOD/ACAD_MATERIAL/ByLayer"),
        "DimStyleHandle": HardPointer(KDimStyle),
        "CmlStyleHandle": HardPointer("NOD/ACAD_MLINESTYLE/Standard"),
    }


# the paper extents contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def PaperExtents(Paper: PaperSize) -> tuple[KPoint, KPoint]:
    return ((0.0, 0.0, 0.0), (Paper.PaperWidth, Paper.PaperHeight, 0.0))


# the space vars contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def SpaceVars(
    Prefix: str, Extents: tuple[KPoint, KPoint], Paper: PaperSize
) -> KVarGroup:
    Origin = (0.0, 0.0, 0.0)
    return {
        Prefix + "InsBase": Origin,
        Prefix + "ExtMin": Extents[0],
        Prefix + "ExtMax": Extents[1],
        Prefix + "LimMin": (0.0, 0.0),
        Prefix + "LimMax": (Paper.PaperWidth, Paper.PaperHeight),
        Prefix + "Elevation": 0.0,
        Prefix + "UcsOrg": Origin,
        Prefix + "UcsXDir": (1.0, 0.0, 0.0),
        Prefix + "UcsYDir": (0.0, 1.0, 0.0),
        Prefix + "UcsNameHandle": KNullHard,
        Prefix + "UcsOrthoRefHandle": KNullHard,
        Prefix + "UcsOrthoView": 0,
        Prefix + "UcsBaseHandle": KNullHard,
        **{Prefix + "UcsOrg" + Corner: Origin for Corner in KUcsCorners},
    }


# the table vars contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def TableVars() -> KVarGroup:
    return {
        **{
            Owner.title().replace("_", "")
            + "ControlHandle": HardOwner("Control:" + Owner)
            for Owner in KTableOwners
        },
        "AppIdControlHandle": HardOwner("Control:APPID"),
        "DimStyleControlHandle": HardOwner("Control:DIMSTYLE"),
        "GroupDictHandle": HardPointer("NOD/ACAD_GROUP"),
        "MlineStyleDictHandle": HardPointer("NOD/ACAD_MLINESTYLE"),
        "NamedObjectsHandle": HardOwner("NOD"),
        "TStackAlign": 1,
        "TStackSize": 70,
        "HyperlinkBase": "",
        "StyleSheet": "",
    }


# the diction vars contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def DictionVars() -> KVarGroup:
    Named: KVarGroup = {
        FieldName: HardPointer("NOD/ACAD_" + Entry)
        for FieldName, Entry in KDictionaries
    }
    return {**Named, "UnknownDictHandle": KNullHard}


# the vars operation needs one geometric convention so native drawing objects use a consistent symbol vocabulary
def UnitVars() -> KVarGroup:
    return {
        "PackedFlags": KLayerWeight | KPlainLines | KLongNames | KNamedPlots,
        "InsUnits": KMillimetreUnits,
        "CePsnType": 0,
        "FingerprintGuid": KZeroGuid,
        "VersionGuid": KZeroGuid,
        "SortEnts": 127,
        "IndexCtl": 0,
        "HideText": 1,
        "XClipFrame": 0,
        "DimAssoc": 2,
        "HaloGap": 0,
        "ObscuredColor": 257,
        "IntersectionColor": 257,
        "ObscuredLtype": 0,
        "IntersectionDisplay": 0,
        "ProjectName": "",
        "PaperSpaceHandle": HardPointer("BLOCK_HEADER:*Paper_Space"),
        "ModelSpaceHandle": HardPointer("BLOCK_HEADER:*Model_Space"),
        "ByLayerHandle": HardPointer("LTYPE:ByLayer"),
        "ByBlockHandle": HardPointer("LTYPE:ByBlock"),
        "ContinuousHandle": HardPointer("LTYPE:Continuous"),
    }


# the closing vars contract needs a shared interpretation so native drawing objects use a consistent symbol vocabulary
def ClosingVars() -> KVarGroup:
    return {
        **KModernVars,
        **KInterfereVars,
        "InterfereObjVsHandle": KNullHard,
        "InterfereVpVsHandle": KNullHard,
        "DragVsHandle": KNullHard,
        "CShadow": 0,
        "UnknownRealF": 0.0,
    }


# the plan header contract needs a stable decomposition so native drawing objects use a consistent symbol vocabulary
def PlanHeader(Paper: PaperSize) -> DraftRecord:
    Values: KVarGroup = {
        **KLegacyHead,
        **KSwitchVars,
        **KCountVars,
        **KSurfaceVars,
        "LtScale": 0.75,
        "TextSize": KTextHeight,
        **KRealVars,
        **KStampVars,
        **CurrentVars(),
        "PsVpScale": 0.0,
        **SpaceVars("P", PaperExtents(Paper), Paper),
        **SpaceVars("", KEmptyBox, Paper),
        **DimensionVars(KTextHeight, KTextStyle),
        **TableVars(),
        **DictionVars(),
        **UnitVars(),
        **ClosingVars(),
    }
    return DraftRecord(tuple(Values.items()))
