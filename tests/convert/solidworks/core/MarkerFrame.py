from struct import pack_into as PackInto

from convert.adapters.solidworks.core.Native import (
    KCircleLocus,
    KCoordinateTag,
    KCurrentMarker,
)

# traversal fixtures share one record size so expected offsets remain comparable
KMarkerSize = 92


# generated marker records expose profile graph boundaries without duplicating saved geometry
def MarkerFrame(
    KindValue: int,
    PointValue: tuple[float, float] | None = None,
    Endpoints: tuple[int, int] | None = None,
) -> bytes:
    Record = bytearray(KMarkerSize)
    Record[: len(KCurrentMarker)] = KCurrentMarker
    PackInto("<I", Record, 17, KindValue)
    Record[23:27] = KCircleLocus if PointValue is None else bytes(4)
    PackInto("<H", Record, 27, 1)
    if PointValue is not None:
        Record[56:58] = KCoordinateTag
        PackInto("<2d", Record, 58, PointValue[0] / 1000, PointValue[1] / 1000)
    if Endpoints is not None:
        PackInto("<HH", Record, 64, *Endpoints)
    Record[-4:] = bytes.fromhex("ffffffff")
    return bytes(Record)
