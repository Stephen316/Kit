from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.Archive import KClassRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.NamedNode import ReadNamedFeat
from convert.adapters.solidworks.resolved.PlaneAtom import ReadPlaneAtom
from convert.adapters.solidworks.resolved.PlaneGeom import (
    DatumData,
    ReadDatumData,
    ReadRefGeom,
)


# the saved datum identity and geometry must remain tied to the same resolved allocation
@Dataclass(frozen=True, slots=True)
class PrincipalDatum:
    NameValue: str
    FeatureId: int
    Offset: int
    EndOffset: int
    ObjectIndex: int
    NextIndex: int
    Geometry: DatumData


# a native principal plane must carry its own named feature and typed default data
def ReadPrincipal(Cursor: ArchiveCursor, KindValue: str) -> PrincipalDatum:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moRefPlane_c",), KindValue, CompactOnly=True
    )
    _ = Cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    NameValue, FeatureId = ReadNamedFeat(Cursor, (0xC0000000,))
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded principal model feature")
    _ = ReadPlaneAtom(Cursor)
    _ = ReadRefGeom(Cursor, 5)
    Geometry = ReadDatumData(Cursor, KindValue)
    return PrincipalDatum(
        NameValue,
        FeatureId,
        Offset,
        Cursor.Offset,
        ObjectIndex,
        Cursor.NextIndex,
        Geometry,
    )
