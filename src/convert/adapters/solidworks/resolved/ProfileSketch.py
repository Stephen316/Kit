from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.sketch.GeometryTypes import Coincidence, SketchGeometry
from convert.adapters.solidworks.sketch.InlineSketch import ParseInlineMut
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpans


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
    Members: MemberSpans


# the profile owns the inline sketch read from its exact saved class reference
def ReadProfileBody(
    Cursor: ArchiveCursor,
    Generation: int,
    *,
    ProfileKind: str = KDefinitionKind,
    EnvironmentLead: int = 6,
) -> ProfileSketch:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moProfileFeature_c",), ProfileKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId, _ = ReadProfileHead(Cursor, (0x40000000, 0xC0000000))
    SketchOffset = Cursor.Offset
    _, _, SketchIndex = Cursor.TakePointer(
        ("sgSketch",), KClassRefKind, CompactOnly=True
    )
    Inline = ParseInlineMut(
        Cursor, SketchOffset, SketchIndex, Generation, EnvironmentLead=EnvironmentLead
    )
    return ProfileSketch(
        NameValue,
        FeatureId,
        ObjectIndex,
        Offset,
        SketchOffset,
        SketchIndex,
        Inline.Geometry,
        Inline.Coincidences,
        Inline.Members,
    )
