from dataclasses import dataclass as DataClass

from ConfigModelOptions import (
    ConfigModelOptions,
    ReadModelOptions,
    RequireOptions,
    WriteModelOptions,
)
from ConfigModelView import KCurvatureClass, KPlaneViewClass, KUnitComponent
from ConfigSectionHatch import (
    KPartMaterial,
    ReadHatch,
    RequireHatch,
    SectionHatch,
    WriteHatch,
)
from HeaderTail import KFrameTolerance, FrameValues, HeaderBounds
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    EncodeNull,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# runtime update bookkeeping comes from its model owner independently of bounds
@DataClass(frozen=True)
class ModelUpdates:
    GeometryStamp: int
    CosmeticFlag: int
    Entries: tuple[tuple[int, int], ...]


# the box is optional and the hatch has distinct presentation ownership
@DataClass(frozen=True)
class ConfigModelBody:
    Bounds: HeaderBounds | None
    Options: ConfigModelOptions
    Updates: ModelUpdates
    Hatch: SectionHatch


# the previous presentation establishes which later class slot belongs to the hatch
def RequirePosition(Generation: int, NextIndex: int, Classes: dict[str, int]) -> None:
    RequireArch(Generation, KConfigGen, "standalone model body generation")
    CurvatureIndex = Classes.get(KCurvatureClass)
    RequireArch(CurvatureIndex in (None, 45), True, "optional curvature allocation")
    PlaneIndex = 45 if CurvatureIndex is None else 47
    RequireArch(
        (Classes.get(KUnitComponent), Classes.get(KPlaneViewClass), NextIndex),
        (43, PlaneIndex, PlaneIndex + 2),
        "model body after plane appearance",
    )


# a single stored cosmetic entry retains both its unsigned stamp and signed flag
def RequireUpdates(State: ModelUpdates) -> None:
    RequireArch(
        type(State.GeometryStamp) is int and 0 <= State.GeometryStamp <= 0xFFFFFFFF,
        True,
        "unsigned model geometry change stamp",
    )
    RequireArch(
        (State.CosmeticFlag, len(State.Entries)) in ((0, 0), (1, 1)),
        True,
        "measured standalone cosmetic update state",
    )
    RequireArch(
        all(
            type(Key) is int and 0 < Key <= 0xFFFFFFFF and Flag == 1
            for Key, Flag in State.Entries
        ),
        True,
        "keyed cosmetic update stamp and flag",
    )


# configuration uses the same bounding box geometry as the independent model header
def ReadModelBounds(Cursor: ArchiveCursor) -> HeaderBounds | None:
    (Present,) = Cursor.ReadInts("<B")
    RequireArch(Present in (0, 1), True, "model bounds presence")
    if not Present:
        return None
    Frame = Cursor.ReadPoint(10)
    Bounds = HeaderBounds(
        (Frame[6], Frame[7], Frame[8]), (Frame[3], Frame[4], Frame[5])
    )
    RequireArch(
        all(
            abs(Filed - Derived) <= KFrameTolerance
            for Filed, Derived in zip(Frame, FrameValues(Bounds), strict=True)
        ),
        True,
        "model bounding box midpoint and corner radius",
    )
    return Bounds


# the counted update map must be bounded before touching the next archive pointer
def ReadModelUpdates(Cursor: ArchiveCursor) -> ModelUpdates:
    Stamp, Flag, Count = Cursor.ReadInts("<I2i")
    RequireArch(Count in (0, 1), True, "model cosmetic update entry count")
    Entries: tuple[tuple[int, int], ...] = ()
    if Count:
        Key, Change = Cursor.ReadInts("<Ii")
        Entries = ((Key, Change),)
    State = ModelUpdates(Stamp, Flag, Entries)
    RequireUpdates(State)
    return State


# the bounded model body must leave the material definition ready for its own reader
def ReadModelBody(Cursor: ArchiveCursor, Generation: int) -> ConfigModelBody:
    Classes = {Name: Index for Index, Name in Cursor.Classes.items()}
    RequirePosition(Generation, Cursor.NextIndex, Classes)
    Bounds = ReadModelBounds(Cursor)
    Options = ReadModelOptions(Cursor)
    Updates = ReadModelUpdates(Cursor)
    Cursor.ReadNull()
    Hatch = ReadHatch(Cursor)
    Material = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        (Material.kind, Material.class_name, Material.schema, Material.wide),
        (KDefinitionKind, KPartMaterial, 1, False),
        "next owned part material definition",
    )
    return ConfigModelBody(Bounds, Options, Updates, Hatch)


# one continuation uses the previous map and derives the saved frame from world bounds
def WriteModelBody(
    Writer: ArchiveWriter, Generation: int, State: ConfigModelBody
) -> None:
    RequirePosition(Generation, Writer.next_index, Writer.classes)
    RequireOptions(State.Options)
    RequireUpdates(State.Updates)
    RequireHatch(State.Hatch)
    Frame = () if State.Bounds is None else FrameValues(State.Bounds)
    RequireArch(len(Frame) in (0, 10), True, "compiled model bounding frame")
    Writer.u8(int(bool(Frame)))
    for Value in Frame:
        Writer.f64(Value)
    WriteModelOptions(Writer, State.Options)
    Writer.u32(State.Updates.GeometryStamp)
    Writer.i32(State.Updates.CosmeticFlag)
    Writer.i32(len(State.Updates.Entries))
    for Key, Change in State.Updates.Entries:
        Writer.u32(Key)
        Writer.i32(Change)
    Writer.raw(EncodeNull())
    WriteHatch(Writer, State.Hatch)
