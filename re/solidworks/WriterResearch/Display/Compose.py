from dataclasses import dataclass as DataClass

from BlindDimension import DimGeometry, WriteDistMut
from Display.Opening import EncodeOpening
from DisplayBaseFields import EncodeBaseEnd, EncodeBaseOpts
from DisplayBaseHead import EncodeBaseHead
from DisplayCache import EncodeBossCache
from DisplayFavorite import KFavoriteClass, WriteFavorMut
from DisplayHandle import KHandleClass, WriteHandleMut
from DisplayMasks import DisplayPrefs
from DisplayReturn import EncodeDistReturn
from DisplayStyle import EncodeBlindBossDisplayAfterStyle, EncodeBlindBossDisplayStyle
from DisplayTail import EncodeBossTail
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the ordinary boss references the display class declared by the preceding sketch
KDisplayClass = "moDisplayDistanceDim_c"
KDisplayMode = 201
KDisplaySchema = 1


# the boss supplies its own feature parameter identity and annotation placement
@DataClass(frozen=True, slots=True, kw_only=True)
class BossDisplay:
    DimensionId: int
    RetainCount: int
    NameValue: str
    DepthMm: float
    Geometry: DimGeometry
    WitnessMetres: float


# document drafting settings are supplied separately from the modeled geometry
@DataClass(frozen=True, slots=True, kw_only=True)
class DisplayDraft:
    Preferences: DisplayPrefs
    Alignment: tuple[int, int]
    Standard: int
    ExtendLeader: bool
    SplitDual: bool
    ArrowHead: int
    Precision: int
    AltPrecision: int


# the ordered display occurrence stops before its owning end specification resumes
def WriteDisplayMut(
    Writer: ArchiveWriter,
    State: BossDisplay,
    Draft: DisplayDraft,
    *,
    Generation: int,
    ConditionOne: bool,
) -> int:
    DisplayIndex = Writer.next_index
    RequireArch(
        all(
            0 < Writer.classes.get(NameValue, 0) < DisplayIndex < KBigObjectTag
            for NameValue in (KDisplayClass, KFavoriteClass)
        )
        and KHandleClass not in Writer.classes,
        True,
        "ordinary blind display enclosing class allocations",
    )
    OpenBytes = (
        EncodeOpening(
            Generation=Generation, DisplayMode=KDisplayMode, ConditionOne=ConditionOne
        )
        + EncodeBlindBossDisplayStyle(
            Generation=Generation, DisplayMode=KDisplayMode, ConditionOne=ConditionOne
        )
        + EncodeBlindBossDisplayAfterStyle(
            Generation=Generation,
            DisplayMode=KDisplayMode,
            ConditionOne=ConditionOne,
            HandleCount=1,
        )
    )
    Placement = EncodeBossTail(
        Generation=Generation,
        DisplayMode=KDisplayMode,
        ConditionOne=ConditionOne,
        Geometry=State.Geometry,
        DepthMm=State.DepthMm,
        WitnessMetres=State.WitnessMetres,
        ArrowHead=Draft.ArrowHead,
        Precision=Draft.Precision,
        AltPrecision=Draft.AltPrecision,
    )
    Cache = EncodeBossCache(
        State.DepthMm / 1000,
        Generation=Generation,
        DisplayMode=KDisplayMode,
        ConditionOne=ConditionOne,
    )
    CloseBytes = (
        EncodeBaseHead(
            Draft.Preferences,
            Draft.Alignment,
            Generation=Generation,
            DisplayMode=KDisplayMode,
            ConditionOne=ConditionOne,
        )
        + EncodeBaseOpts(
            Draft.Preferences,
            Draft.Standard,
            Draft.ExtendLeader,
            Draft.SplitDual,
            Generation=Generation,
            DisplayMode=KDisplayMode,
            ConditionOne=ConditionOne,
        )
        + EncodeBaseEnd(
            Generation=Generation, DisplayMode=KDisplayMode, ConditionOne=ConditionOne
        )
        + EncodeDistReturn(
            Generation=Generation, DisplayMode=KDisplayMode, ConditionOne=ConditionOne
        )
    )
    Writer.begin_object(KDisplayClass, KDisplaySchema)
    Writer.raw(OpenBytes)
    _ = WriteHandleMut(Writer, Generation=Generation, ConditionOne=ConditionOne)
    _ = WriteDistMut(
        Writer,
        Generation=Generation,
        ConditionOne=ConditionOne,
        DimensionId=State.DimensionId,
        RetainCount=State.RetainCount,
        NameValue=State.NameValue,
        DepthMm=State.DepthMm,
        Geometry=State.Geometry,
    )
    Writer.raw(Placement)
    Writer.raw(Cache)
    _ = WriteFavorMut(
        Writer,
        Generation=Generation,
        DisplayMode=KDisplayMode,
        ConditionOne=ConditionOne,
    )
    Writer.raw(CloseBytes)
    return DisplayIndex
