from math import isclose as IsClose
from typing import TypedDict

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPose


# the face transform preserves the distinction between absent and encoded basis values
class FacePose(TypedDict):
    basis: tuple[float, ...] | None
    translation_scale: tuple[float, ...]


# the saved frame carries its plane point and normal independently of the transform
class FaceFrame(TypedDict):
    root_metres: tuple[float, ...]
    normal_world: tuple[float, ...]
    transform: FacePose
    border_metres: tuple[float, ...]


# both plane and wrapper transforms must use the checked local pose framing
def ReadFacePose(Cursor: ArchiveCursor) -> FacePose:
    BasisValue, ShiftScale = ReadLocalPose(Cursor)
    return {"basis": BasisValue, "translation_scale": ShiftScale}


# the plane record locates the bound face before its nested component identity
def ReadFaceFrame(Cursor: ArchiveCursor) -> FaceFrame:
    RootPoint = Cursor.ReadPoint(3)
    Normal = Cursor.ReadPoint(3)
    RequireArch(
        IsClose(sum(Value * Value for Value in Normal), 1.0), True, "unit plane normal"
    )
    Transform = ReadFacePose(Cursor)
    Border = Cursor.ReadPoint(4)
    Cursor.ReadNull()
    _ = Cursor.ReadInts("<3iB2i")
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent extra plane payload")
    for _ in range(3):
        Cursor.ReadNull()
    return {
        "root_metres": RootPoint,
        "normal_world": Normal,
        "transform": Transform,
        "border_metres": Border,
    }


# the enclosing wrapper must corroborate the same point and normal before it returns
def CloseFaceFrame(Cursor: ArchiveCursor, Frame: FaceFrame) -> None:
    RequireArch(Cursor.ReadInts("<H"), (1,), "local reference wrapper mode")
    Cursor.ReadNull()
    _ = Cursor.ReadInts("<2i")
    RequireArch(Cursor.ReadInts("<2H"), (0, 0), "absent reference wrapper transforms")
    _ = Cursor.ReadInts("<11i")
    _ = Cursor.ReadPoint(4)
    RequireArch(Cursor.ReadPoint(3), Frame["root_metres"], "same wrapper root point")
    RequireArch(Cursor.ReadPoint(3), Frame["normal_world"], "same wrapper normal")
    _ = ReadFacePose(Cursor)
    _ = Cursor.ReadPoint(3)
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<4i"), (0, 1, 0, 0), "guarded face plane trailer")
