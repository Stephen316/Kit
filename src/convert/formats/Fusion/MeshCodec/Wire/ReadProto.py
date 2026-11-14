from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField
from convert.formats.Fusion.MeshCodec.Wire.ReadVarint import ReadVarint


def ReadProto(Payload: bytes) -> tuple[ProtoField, ...]:
    Cursor = ByteCursor(Payload)
    Result: list[ProtoField] = []
    while Cursor.Remaining():
        Value = ReadVarint(Cursor)
        Number, Width = Value >> 3, Value & 7
        if not 0 < Number < 1 << 29:
            raise ValueError("Invalid Fusion mesh protobuf field")
        if Width == 0:
            Result.append(ProtoField(Number, ReadVarint(Cursor)))
        elif Width == 2:
            Result.append(ProtoField(Number, Cursor.TakeBytes(ReadVarint(Cursor))))
        else:
            raise ValueError("Unsupported Fusion mesh protobuf wire type")
    return tuple(Result)
