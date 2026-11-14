from struct import calcsize as SizeOf
from struct import error as StructError
from struct import pack as PackFields
from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
    KDwgValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsFloat,
    AsInt,
    AsPoint,
    AsText,
)

KGroupRanges = (
    (0, 9, "Text"),
    (10, 18, "Point"),
    (38, 59, "<d"),
    (60, 79, "<h"),
    (90, 99, "<i"),
    (100, 109, "Text"),
    (140, 149, "<d"),
    (160, 169, "<q"),
    (170, 179, "<h"),
    (270, 279, "<h"),
    (280, 299, "<B"),
    (300, 309, "Text"),
    (310, 319, "Chunk"),
    (320, 369, "<Q"),
    (370, 389, "<h"),
    (390, 399, "<Q"),
    (400, 409, "<h"),
    (410, 419, "Text"),
    (420, 459, "<i"),
    (460, 469, "<d"),
    (470, 479, "Text"),
    (480, 481, "<Q"),
)


def GroupLayout(GroupCode: int) -> str:
    for LowCode, HighCode, Layout in KGroupRanges:
        if LowCode <= GroupCode <= HighCode:
            return Layout
    raise ValueError(f"DWG xrecord group code {GroupCode} is unsupported")


def ReadGroupValue(
    DataValue: bytes, Position: int, Layout: str
) -> tuple[KDwgValue, int]:
    if Layout == "Text":
        Count = UnpackFrom("<H", TakeSpan(DataValue, Position, 2, "xrecord text"))[0]
        Encoded = TakeSpan(DataValue, Position + 2, Count * 2, "xrecord text")
        return Encoded.decode("utf-16-le"), Position + 2 + Count * 2
    if Layout == "Chunk":
        Count = TakeSpan(DataValue, Position, 1, "xrecord chunk")[0]
        Chunk = TakeSpan(DataValue, Position + 1, Count, "xrecord chunk")
        return Chunk, Position + 1 + Count
    if Layout == "Point":
        Packed = TakeSpan(DataValue, Position, 24, "xrecord point")
        return tuple(float(Element) for Element in UnpackFrom("<3d", Packed)), (
            Position + 24
        )
    Packed = TakeSpan(DataValue, Position, SizeOf(Layout), "xrecord value")
    Value = UnpackFrom(Layout, Packed)[0]
    return (float(Value) if Layout == "<d" else int(Value)), Position + len(Packed)


def ReadGroupItems(DataValue: bytes) -> DwgRecord:
    Fields: list[DwgField] = []
    Position = 0
    while Position < len(DataValue):
        Opening = TakeSpan(DataValue, Position, 2, "xrecord group code")
        GroupCode = UnpackFrom("<H", Opening)[0]
        Value, Position = ReadGroupValue(
            DataValue, Position + 2, GroupLayout(GroupCode)
        )
        Fields.append(DwgField(str(GroupCode), Value))
    return DwgRecord(tuple(Fields))


def EncodeGroup(GroupCode: int, Value: KDwgValue) -> bytes:
    Layout = GroupLayout(GroupCode)
    if Layout == "Text":
        Encoded = AsText(Value).encode("utf-16-le")
        return PackFields("<H", len(Encoded) // 2) + Encoded
    if Layout == "Chunk":
        Chunk = AsBytes(Value)
        if len(Chunk) > 255:
            raise ValueError("DWG xrecord binary chunk exceeds 255 bytes")
        return bytes((len(Chunk),)) + Chunk
    if Layout == "Point":
        return PackFields("<3d", *AsPoint(Value, 3))
    if Layout == "<d":
        return PackFields(Layout, AsFloat(Value))
    return PackFields(Layout, AsInt(Value))


def EncodeGroups(GroupItems: DwgRecord) -> bytes:
    Encoded = bytearray()
    for Entry in GroupItems.RecordFields:
        if not Entry.FieldName.isdigit():
            raise ValueError(f"DWG xrecord field {Entry.FieldName!r} is no group code")
        GroupCode = int(Entry.FieldName)
        try:
            Encoded += PackFields("<H", GroupCode)
            Encoded += EncodeGroup(GroupCode, Entry.FieldValue)
        except StructError as Failure:
            raise ValueError("DWG xrecord value is out of range") from Failure
    return bytes(Encoded)
