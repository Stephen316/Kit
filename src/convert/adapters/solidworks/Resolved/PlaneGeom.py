from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPose


# a principal datum must retain the actual saved orientation and its archive identity
@Dataclass(frozen=True, slots=True)
class DatumData:
    ObjectIndex: int
    PointMetres: tuple[float, ...]
    NormalWorld: tuple[float, ...]
    BasisValue: tuple[float, ...] | None
    ShiftScale: tuple[float, ...]


# the geometry mode selects the immediately following reference plane record
def ReadRefGeom(Cursor: ArchiveCursor, ExpectedMode: int) -> tuple[float, ...]:
    PointValue = Cursor.ReadPoint(3)
    ModeValue, _ = Cursor.ReadInts("<2i")
    RequireArch(ModeValue, ExpectedMode, "supported plane geometry mode")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded plane geometry trailer")
    return PointValue


# geometry verification needs the origin and normal from the decoded datum itself
def ReadDatumData(Cursor: ArchiveCursor, KindValue: str) -> DatumData:
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moDefaultRefPlnData_c",), KindValue, CompactOnly=True
    )
    PointMetres = Cursor.ReadPoint(3)
    NormalWorld = Cursor.ReadPoint(3)
    BasisValue, ShiftScale = ReadLocalPose(Cursor)
    _ = Cursor.ReadPoint(4)
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<3iB"), (0, -4, -4, 0), "guarded default plane fields")
    _ = Cursor.ReadPoint(3)
    RequireArch(Cursor.ReadInts("<2iH"), (1, 0, 0), "guarded default plane scalar tail")
    for _ in range(3):
        Cursor.ReadNull()
    return DatumData(ObjectIndex, PointMetres, NormalWorld, BasisValue, ShiftScale)
