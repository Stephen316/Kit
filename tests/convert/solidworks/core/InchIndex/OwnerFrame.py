from struct import pack as PackBytes

from convert.adapters.solidworks.container.Format import KSerializedStringMarker


def OwnerFrame(NameValue: str, ObjectId: int) -> bytes:
    return (
        PackBytes("<H", 32772)
        + KSerializedStringMarker
        + bytes((len(NameValue),))
        + NameValue.encode("utf-16le")
        + PackBytes("<III", 0, 0, ObjectId)
    )
