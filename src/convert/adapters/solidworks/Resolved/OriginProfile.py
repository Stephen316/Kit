from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.OriginDisplay import (
    OriginList,
    ReadOrigViewMut,
)
from convert.adapters.solidworks.Resolved.PrincipalRef import PrincipalRef, ReadPlaneRef
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimFields import ReadDimBase
from convert.adapters.solidworks.Sketch.Members import ReadPointMut
from convert.adapters.solidworks.Sketch.Relations import ReadDims


# the origin point handle must retain the local geometry identity before a user sketch opens
@Dataclass(frozen=True, slots=True)
class OriginGeometry:
    Offset: int
    EndOffset: int
    PointValue: tuple[float, ...]
    RelationType: int
    Handle: int


# the origin allocation links its geometry and presentation to the principal support
@Dataclass(frozen=True, slots=True)
class OriginProfile:
    NameValue: str
    FeatureId: int
    Offset: int
    ObjectIndex: int
    SketchOffset: int
    SketchIndex: int
    Geometry: OriginGeometry
    Lists: tuple[OriginList, OriginList]
    DisplayEnd: int
    Support: PrincipalRef
    StateValue: int
    EndOffset: int
    NextIndex: int


# the origin relation must select the point inside its own inline sketch body
def ReadOrigGeoMut(Cursor: ArchiveCursor) -> OriginGeometry:
    Sketch = SketchArchive(Cursor)
    Offset = Sketch.Offset
    RequireArch(Sketch.ReadCount(), 1, "one origin point")
    _, _, PointValue = ReadPointMut(Sketch)
    RequireArch(PointValue, (0, 0), "origin point coordinates")
    RequireArch(Sketch.ReadCount(), 0, "empty origin lines")
    ReadDims(Sketch)
    RequireArch(Sketch.Dimensions, [], "empty origin value dimensions")
    RequireArch(Sketch.ReadInts("<3H"), (0, 0, 1), "one origin member relation")
    _, _, RelationType = ReadDimBase(Sketch, None)
    RequireArch(RelationType, 17, "witnessed origin relation type")
    RequireArch(Sketch.ReadInts("<2H"), (65534, 0), "guarded origin relation fields")
    Handle = Sketch.ReadObject("sgPointHandle")
    RequireArch(
        Sketch.Handles.get(Handle),
        (0, -1, 0),
        "relation targets the local origin point",
    )
    Cursor.Offset = Sketch.Offset
    Cursor.NextIndex = Sketch.NextIndex
    return OriginGeometry(Offset, Sketch.Offset, PointValue, RelationType, Handle)


# the origin uses the saved datum reference and must reach its complete feature return
def ReadOriginTail(Cursor: ArchiveCursor, Generation: int) -> tuple[PrincipalRef, int]:
    Cursor.ReadNull()
    Support = ReadPlaneRef(Cursor, Generation, KDefinitionKind)
    RequireArch(Support.AxisCode, 3, "guarded origin plane direction state")
    RequireArch(
        (Support.BasisValue, Support.ShiftScale),
        (None, (0, 0, 0, 1)),
        "origin identity placement",
    )
    RequireArch(Cursor.ReadInts("<2H"), (0, 4), "guarded origin outer flags")
    Cursor.ReadNull()
    Marker, AuxValue, StateValue, Count = Cursor.ReadInts("<2iIH")
    RequireArch((Marker, AuxValue, Count), (-7, 0, 0), "modern origin feature trailer")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2Hi"), (0, 0, 0), "empty origin final groups")
    return Support, StateValue


# walking the actual origin allocations preserves the map at the first authored feature
def ReadOrigin(Cursor: ArchiveCursor, Generation: int) -> OriginProfile:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moOriginProfileFeature_c",), KDefinitionKind, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId, _ = ReadProfileHead(Cursor, (0xC0000000,))
    RequireArch((NameValue, FeatureId), ("Origin", 5), "typed origin profile")
    SketchOffset = Cursor.Offset
    SketchKind = (
        KClassRefKind if "sgSketch" in Cursor.Classes.values() else KDefinitionKind
    )
    _, _, SketchIndex = Cursor.TakePointer(("sgSketch",), SketchKind, CompactOnly=True)
    Geometry = ReadOrigGeoMut(Cursor)
    Lists = ReadOrigViewMut(Cursor)
    DisplayEnd = Cursor.Offset
    Support, StateValue = ReadOriginTail(Cursor, Generation)
    return OriginProfile(
        NameValue,
        FeatureId,
        Offset,
        ObjectIndex,
        SketchOffset,
        SketchIndex,
        Geometry,
        Lists,
        DisplayEnd,
        Support,
        StateValue,
        Cursor.Offset,
        Cursor.NextIndex,
    )
