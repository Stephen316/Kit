from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.sketch.GeometryTypes import Coincidence, SketchGeometry
from convert.adapters.solidworks.sketch.InlineSketch import ReadInlineMut


# typed inline geometry belongs to the surrounding profile feature rather than the archive counter
@Dataclass(frozen=True, slots=True)
class ProfileSketch:
    NameValue: str
    FeatureId: int
    ObjectIndex: int
    Offset: int
    SketchOffset: int
    SketchIndex: int
    Geometry: SketchGeometry
    Coincidences: list[Coincidence]


# the profile owns the inline sketch read from its exact saved class reference
def ReadProfileBody(Cursor: ArchiveCursor, Generation: int) -> ProfileSketch:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moProfileFeature_c",), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId, _ = ReadProfileHead(Cursor, (0x40000000, 0xC0000000))
    SketchOffset = Cursor.Offset
    _, _, SketchIndex = Cursor.TakePointer(
        ("sgSketch",), KClassRefKind, CompactOnly=True
    )
    Geometry, Coincidences = ReadInlineMut(
        Cursor, SketchOffset, SketchIndex, Generation
    )
    return ProfileSketch(
        NameValue,
        FeatureId,
        ObjectIndex,
        Offset,
        SketchOffset,
        SketchIndex,
        Geometry,
        Coincidences,
    )
