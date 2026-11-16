from struct import pack as PackFields
from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.Archive import ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.BossDepth import DepthDisplay
from convert.adapters.solidworks.Resolved.BossEnd import ReadBossClose
from tests.Research.Archives.SolidWorksCacheVerify import KFavoriteClass, KFavoriteName
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut
from tests.Research.Archives.SolidWorksDistInputs import ReadDistInputs
from tests.Research.Archives.SolidWorksDistVerify import (
    KAuthoredWitness,
    KModelIdentity,
    KParentClasses,
    KRetainCount,
)


# hosted import keeps the whole research constructor outside the installed namespace
class DisplayCodec(Protocol):

    # each nested constructor accepts explicit authored settings or geometry
    def DimGeometry(self, *Values: object) -> object: ...

    # document preferences remain a typed input to the composition
    def DisplayPrefs(self, **Values: bool) -> object: ...

    # the caller owns the model identity and annotation placement
    def BossDisplay(self, **Values: object) -> object: ...

    # draft preferences are independent of the length parameter
    def DisplayDraft(self, **Values: object) -> object: ...

    # the shared writer retains its next object index at the end of the display
    def WriteDisplayMut(
        self,
        Writer: ArchiveWriter,
        State: object,
        Draft: object,
        *,
        Generation: int,
        ConditionOne: bool,
    ) -> int: ...


# load dependencies in constructor order without changing the broader import path
def LoadDisplayMut(PatchValue: MonkeyPatch) -> DisplayCodec:
    for ModuleName in (
        "BlindDepth",
        "DisplayHandle",
        "BlindDimension",
        "DisplayFavorite",
        "DisplayMasks",
        "DisplayForeshorten",
        "DisplayBaseHead",
        "DisplayBaseFields",
        "DisplayCache",
        "DisplayReturn",
        "DisplayStyle",
        "DisplayTail",
        "Display.Opening",
    ):
        _ = LoadResearchMut(PatchValue, ModuleName)
    return CastValue(DisplayCodec, LoadResearchMut(PatchValue, "Display.Compose"))


# the anchored comparison checks all emitted bytes around four known input or state differences
def MatchDisplay(
    Emitted: bytes, Saved: bytes, Depth: DepthDisplay, Reloaded: bool
) -> None:
    CacheStart = Depth["dimension"]["end"] - Depth["offset"]
    FavoriteStart = CacheStart + 92
    WitnessAt = CacheStart - 240 + 54
    NativeMask = 0x82000427 if Reloaded else 0x80000427
    Differences = (
        (WitnessAt, "<d", None, KAuthoredWitness),
        (CacheStart + 32, "<I", NativeMask, 0x80000427),
        (FavoriteStart + 156, "<I", 32763, 0),
        (FavoriteStart + 344, "<i", 6029357, 0),
    )
    LastIndex = 0
    for Index, Shape, Original, Expected in Differences:
        assert Emitted[LastIndex:Index] == Saved[LastIndex:Index]
        Native = FieldCursor(Saved, Index)
        (Observed,) = Native.ReadValue(Shape)
        if Original is None:
            assert Observed != Expected
        else:
            assert Observed == Original
        assert Emitted[Index : Native.Offset] == PackFields(Shape, Expected)
        LastIndex = Native.Offset
    assert Emitted[LastIndex:] == Saved[LastIndex:]


# an explicit neutral geometry and annotation input exercise the real research composition
def MakeDisplay(
    PatchValue: MonkeyPatch,
    Writer: ArchiveWriter,
    Variant: str,
    Generation: int,
    Measurements: bytes,
) -> int:
    Codec = LoadDisplayMut(PatchValue)
    Measure = ReadDistInputs(Measurements, Variant)
    Geometry = Codec.DimGeometry(
        Measure["frame"], Measure["normal"], Measure["tangent"], Measure["reverse"]
    )
    State = Codec.BossDisplay(
        DimensionId=KModelIdentity,
        RetainCount=KRetainCount,
        NameValue=Measure["name"],
        DepthMm=Measure["depth_mm"],
        Geometry=Geometry,
        WitnessMetres=KAuthoredWitness,
    )
    Prefs = Codec.DisplayPrefs(
        design_intent=True,
        inward_tolerance_rounding=False,
        remove_zero=False,
        uppercase_dimension=False,
    )
    Draft = Codec.DisplayDraft(
        Preferences=Prefs,
        Alignment=(1, 1),
        Standard=4,
        ExtendLeader=True,
        SplitDual=False,
        ArrowHead=0,
        Precision=2,
        AltPrecision=2,
    )
    return Codec.WriteDisplayMut(
        Writer, State, Draft, Generation=Generation, ConditionOne=False
    )


# the packaged owner must reach its original return after consuming the generated child
def VerifyDisplay(
    PatchValue: MonkeyPatch,
    Variant: str,
    Resolved: bytes,
    Generation: int,
    Depth: DepthDisplay,
    Measurements: bytes,
) -> None:
    Writer = ArchiveWriter()
    Begin, EndOffset = Depth["offset"], Depth["end"]
    DisplayObject = Depth["object_index"]
    DisplayName = "moDisplayDistanceDim_c"
    Writer.classes.update(KParentClasses)
    Writer.classes[DisplayName] = ReadTag(Resolved, Begin).index
    Writer.classes[KFavoriteName] = KFavoriteClass
    Writer.SetNextIndex(DisplayObject)
    ParentClasses = {Index: NameValue for NameValue, Index in Writer.classes.items()}
    assert (
        MakeDisplay(PatchValue, Writer, Variant, Generation, Measurements)
        == DisplayObject
    )
    Emitted = Writer.build()
    assert len(Emitted) == EndOffset - Begin == 1807
    assert (DisplayObject, Writer.next_index) == (296, 304)
    MatchDisplay(
        Emitted,
        Resolved[Begin:EndOffset],
        Depth,
        Variant not in ("baseline-a", "plane-yz", "direction-negative"),
    )

    Native = ArchiveCursor(Resolved, Begin, DisplayObject, ParentClasses.copy(), {})
    SourceClose = ReadBossClose(Native)
    Generated = ArchiveCursor(
        Emitted + Resolved[EndOffset:], 0, DisplayObject, ParentClasses, {}
    )
    Close = ReadBossClose(Generated)
    assert Close["depth_display"]["end"] == len(Emitted)
    assert Close["depth_display"]["cached_metres"] == Depth["cached_metres"]
    assert (Close["from_end_object"], Generated.NextIndex) == (
        SourceClose["from_end_object"],
        306,
    )
    assert Generated.Objects == Native.Objects
    assert Generated.Classes == Native.Classes
    assert Close["end"] == SourceClose["end"] - Begin == 1807 + 121 + 12
    assert Generated.ReadInts("<i") == (0,)
    assert Generated.Offset == len(Generated.BlobValue)
