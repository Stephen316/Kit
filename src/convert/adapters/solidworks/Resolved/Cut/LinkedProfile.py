from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KObjectRefKind
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead


# later sketches keep their configuration geometry identity alongside the resolved owner
@Dataclass(frozen=True, slots=True)
class LinkedProfile:
    Offset: int
    ObjectIndex: int
    NameValue: str
    FeatureId: int
    EarlyOffset: int
    SketchOffset: int
    SketchIndex: int


# an equation bearing profile refers to an already allocated configuration sketch
def ReadLinkedProf(Cursor: ArchiveCursor, KindValue: str) -> LinkedProfile:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moProfileFeature_c",), KindValue, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId, EarlyOffset = ReadProfileHead(
        Cursor, (0x40000000, 0xC0000000)
    )
    SketchOffset = Cursor.Offset
    _, _, SketchIndex = Cursor.TakePointer(
        ("sgSketch",), KObjectRefKind, CompactOnly=True
    )
    return LinkedProfile(
        Offset,
        ObjectIndex,
        NameValue,
        FeatureId,
        EarlyOffset,
        SketchOffset,
        SketchIndex,
    )
