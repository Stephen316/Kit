from struct import pack as PackBytes, pack_into as PackInto

from convert.adapters.solidworks.Container.Format import (
    KDimensionScalarHeaders,
    KSerializedStringMarker,
)


# synthetic scalar records isolate identity and role requirements at the decoder boundary
def ScalarFrame(
    NameValue: str, NativeValue: float, ObjectId: int | None, RoleValue: int
) -> bytes:
    Trailer = bytearray(51)
    PackInto("<I", Trailer, 3, 4294967295 if ObjectId is None else ObjectId)
    Trailer[21:27] = bytes((1, 0, 0, 0, 2, 0))
    Trailer[27] = RoleValue
    PackInto("<HHI", Trailer, 35, 2, 7, 4294967295)
    PackInto("<HHI", Trailer, 43, 3, 9, 4294967295)
    return (
        PackBytes("<H", 32772)
        + KSerializedStringMarker
        + bytes((len(NameValue),))
        + NameValue.encode("utf-16le")
        + KDimensionScalarHeaders[0]
        + PackBytes("<d", NativeValue)
        + bytes(Trailer)
    )
