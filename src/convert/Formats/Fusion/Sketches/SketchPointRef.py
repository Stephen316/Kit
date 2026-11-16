from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.Models.VectorPlane import PlaneVector


# curve endpoint references must resolve inside the owning sketch point table
def ReadPointRef(
    BodyValue: bytes, Offset: int, Points: dict[int, PlaneVector]
) -> tuple[int, PlaneVector]:
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = Offset
    Identity = ReadNativeRef(Cursor)
    PointValue = Points.get(Identity)
    if PointValue is None:
        raise ValueError("Missing same-sketch Fusion curve point")
    return Identity, PointValue
