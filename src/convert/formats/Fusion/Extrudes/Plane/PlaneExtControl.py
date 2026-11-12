from math import isclose as IsClose
from struct import unpack as Unpack

from convert.formats.Fusion.Extrudes.Plane.PlaneExtFields import PlaneExtFields
from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.formats.Fusion.MetaCursor import MetaCursor


# literal control slots distinguish a selected start from a selected end
def ReadPlaneCtrl(Cursor: MetaCursor) -> PlaneExtFields:
    if Cursor.TakeBytes(6) != b"\0\1" + bytes(4):
        raise ValueError("Unsupported Fusion selected plane Extrude prefix")
    SourceId = ReadOptRefMut(Cursor)
    IsStart = SourceId is not None
    if (
        Cursor.TakeBytes(2) != bytes(2)
        or Cursor.ReadWord() != 4
        or Cursor.ReadWord() != 1
        or Cursor.ReadWord() != (2 if IsStart else 1)
        or Cursor.TakeBytes(2) != b"\0\1"
        or Cursor.ReadWord() != (2 if IsStart else 0)
    ):
        raise ValueError("Unsupported Fusion selected plane Extrude header")
    AxisX, AxisY, AxisZ = Unpack("<3d", Cursor.TakeBytes(24))
    if not IsClose(
        AxisX * AxisX + AxisY * AxisY + AxisZ * AxisZ,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("Invalid Fusion selected plane Extrude direction")
    StartId = ReadOptRefMut(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion selected plane Extrude second distance")
    AlongId = ReadOptRefMut(Cursor)
    CacheId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError(
            "Unsupported Fusion selected plane Extrude secondary descriptor"
        )
    TaperId = ReadNativeRef(Cursor)
    TargetId = ReadOptRefMut(Cursor)
    Condition = Cursor.ReadWord()
    OffsetId = ReadOptRefMut(Cursor)
    FlagValue = Cursor.ReadWord()
    if Cursor.TakeBytes(16) != bytes(16):
        raise ValueError("Unsupported Fusion selected plane Extrude second extent")
    if (
        SourceId is not None
        and StartId is not None
        and AlongId is not None
        and TargetId is None
        and OffsetId is None
        and (Condition, FlagValue) == (1, 0)
    ):
        return PlaneExtFields(
            "start", SourceId, StartId, AlongId, TaperId, CacheId, (AxisX, AxisY, AxisZ)
        )
    if (
        SourceId is None
        and StartId is None
        and AlongId is None
        and TargetId is not None
        and OffsetId is not None
        and (Condition, FlagValue) == (2, 1)
    ):
        return PlaneExtFields(
            "end", TargetId, OffsetId, None, TaperId, CacheId, (AxisX, AxisY, AxisZ)
        )
    raise ValueError("Unsupported Fusion selected plane Extrude control combination")
