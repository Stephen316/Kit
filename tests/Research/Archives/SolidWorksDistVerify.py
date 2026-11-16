from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.Archive import KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.BossDepth import (
    DepthDisplay,
    ReadFeatHandle,
    ReadParDepthMut,
)
from tests.Research.Archives.SolidWorksDistCodecs import LoadPairMut
from tests.Research.Archives.SolidWorksDistInputs import ReadDistInputs

# the prior archive walk independently bounded the optional point mask for every save
KDistanceEnds = {
    "baseline-a": 14130,
    "baseline-b": 14358,
    "edit-width_mm-41": 14358,
    "edit-height_mm-23": 14358,
    "edit-depth_mm-12": 14358,
    "units-inch": 14358,
    "plane-yz": 14200,
    "direction-negative": 14128,
}

# the enclosing archive establishes these classes before the first feature handle
KParentClasses = {"moNodeName_c": 4, "moLengthParameter_c": 200}

# the measured first handle begins with the next free class slot in its enclosure
KHandleSlot = 297

# the fixture supplies its allocated model identity and the native reference count
KModelIdentity = 29

# the second native retain site is unresolved so the fixture supplies the observed count
KRetainCount = 2


# the writers receive the saved enclosure allocations and independent authored inputs
def GeneratePair(
    PatchValue: MonkeyPatch, Measurements: bytes, Variant: str, Generation: int
) -> tuple[bytes, bytes]:
    Inputs = ReadDistInputs(Measurements, Variant)
    Handle, Distance = LoadPairMut(PatchValue)
    Writer = ArchiveWriter()
    Writer.classes.update(KParentClasses)
    Writer.SetNextIndex(KHandleSlot)
    HandleObject = Handle.WriteHandleMut(
        Writer, Generation=Generation, ConditionOne=False
    )
    assert (HandleObject, Writer.next_index) == (298, 299)
    HandleBytes = Writer.build()
    Geometry = Distance.DimGeometry(
        Inputs["frame"], Inputs["normal"], Inputs["tangent"], Inputs["reverse"]
    )
    DistanceObject = Distance.WriteDistMut(
        Writer,
        Generation=Generation,
        ConditionOne=False,
        DimensionId=KModelIdentity,
        RetainCount=KRetainCount,
        NameValue=Inputs["name"],
        DepthMm=Inputs["depth_mm"],
        Geometry=Geometry,
    )
    assert (DistanceObject, Writer.next_index) == (300, 303)
    return HandleBytes, Writer.build()[len(HandleBytes) :]


# the production reader resumes past the child only with the separate presentation fields
def ReadGenerated(
    Depth: DepthDisplay, HandleBytes: bytes, DistanceBytes: bytes, OuterDisplay: bytes
) -> None:
    Cursor = ArchiveCursor(
        HandleBytes + DistanceBytes + OuterDisplay,
        0,
        KHandleSlot,
        {Slot: ClassName for ClassName, Slot in KParentClasses.items()},
        {},
    )
    Handle = ReadFeatHandle(Cursor, KDefinitionKind)
    assert Handle["object_index"] == Depth["handle"]["object_index"]
    assert Cursor.Offset == len(HandleBytes)
    Dimension = ReadParDepthMut(Cursor, KDefinitionKind)
    SourceStart = Depth["handle"]["offset"]
    Expected = Depth["dimension"].copy()
    Expected["offset"] -= SourceStart
    Expected["value_offset"] -= SourceStart
    Expected["end"] -= SourceStart
    assert Dimension == Expected
    assert Cursor.Offset == len(Cursor.BlobValue)
    assert Cursor.NextIndex == 303
    assert Cursor.Objects[302] == "moNodeName_c"


# archive spans checked separately keep a matching serialization from swallowing display fields
def VerifyDistChild(
    PatchValue: MonkeyPatch,
    Variant: str,
    Resolved: bytes,
    Generation: int,
    Depth: DepthDisplay,
    Measurements: bytes,
) -> None:
    SourceHandle = Depth["handle"]["offset"]
    SourceChild = Depth["dimension"]["offset"]
    ChildEnd = KDistanceEnds[Variant]
    DisplayEnd = Depth["dimension"]["end"]
    assert (
        SourceChild - SourceHandle,
        ChildEnd - SourceChild,
        DisplayEnd - ChildEnd,
    ) == (133, 346, 240)
    HandleBytes, DistanceBytes = GeneratePair(
        PatchValue, Measurements, Variant, Generation
    )
    assert HandleBytes == Resolved[SourceHandle:SourceChild]
    assert DistanceBytes == Resolved[SourceChild:ChildEnd]
    ReadGenerated(Depth, HandleBytes, DistanceBytes, Resolved[ChildEnd:DisplayEnd])
