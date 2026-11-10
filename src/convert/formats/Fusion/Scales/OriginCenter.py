# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import KOriginGuid
from convert.formats.Fusion.Scales.PointBackend import ReadSpatialPt
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from interchange.geometry.models.VectorSpace import SpaceVector

# origin and authored construction points use the same geometry class
KWorkPoint = "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F"


# the named origin point must be a reciprocal member of the selected component origin
def ReadOriginPt(
    BulkData: bytes, Owners: dict[int, RecordSpan], PointId: int, ComponentId: int
) -> SpaceVector:
    Cursor = SelectCursor(BulkData, Owners, PointId, KWorkPoint)
    if len(Cursor.DataValue) != 146 or ReadGeomAttrs(Cursor) != {"EntityGenesis": 0}:
        raise ValueError("Unsupported Fusion origin point")
    Point = ReadSpatialPt(Cursor)
    _ = Cursor.TakeBytes(10)
    if Cursor.ReadText(True, Maximum=1) != "O" or Point != SpaceVector(0.0, 0.0, 0.0):
        raise ValueError("Fusion selected origin point label or coordinates disagree")
    Cursor.Offset = 135
    ContainerId = ReadNativeRef(Cursor)
    Container = SelectCursor(BulkData, Owners, ContainerId, KOriginGuid)
    if (
        len(Container.DataValue) != 96
        or Container.TakeBytes(4) != bytes(4)
        or Container.ReadWord() != 7
    ):
        raise ValueError("Unsupported Fusion origin point container")
    Members = {ReadNativeRef(Container) for _ in range(7)}
    if (
        len(Members) != 7
        or PointId not in Members
        or ReadNativeRef(Container) != ComponentId
    ):
        raise ValueError("Fusion origin point belongs to another component")
    return Point
