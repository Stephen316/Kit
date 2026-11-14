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

KFixedSizes = {2: "<B", 40: "<d", 41: "<d", 42: "<d", 70: "<H", 71: "<I"}


def ReadEedValue(
    DataValue: bytes, Position: int, ItemCode: int
) -> tuple[KDwgValue, int]:
    if ItemCode == 0:
        Count = UnpackFrom("<H", TakeSpan(DataValue, Position, 2, "EED text"))[0]
        Encoded = TakeSpan(DataValue, Position + 2, Count * 2, "EED text")
        return Encoded.decode("utf-16-le"), Position + 2 + Count * 2
    if ItemCode in (3, 5):
        return TakeSpan(DataValue, Position, 8, "EED handle"), Position + 8
    if ItemCode == 4:
        Count = TakeSpan(DataValue, Position, 1, "EED binary")[0]
        return (
            TakeSpan(DataValue, Position + 1, Count, "EED binary"),
            Position + 1 + Count,
        )
    if 10 <= ItemCode <= 13:
        Points = UnpackFrom("<3d", TakeSpan(DataValue, Position, 24, "EED point"))
        return tuple(float(Element) for Element in Points), Position + 24
    Layout = KFixedSizes.get(ItemCode)
    if Layout is None:
        raise ValueError(f"DWG extended data item code {ItemCode} is unsupported")
    SpanBytes = TakeSpan(DataValue, Position, len(PackFields(Layout, 0)), "EED value")
    Value = UnpackFrom(Layout, SpanBytes)[0]
    return (float(Value) if Layout == "<d" else int(Value)), Position + len(SpanBytes)


def ReadEedItems(DataValue: bytes) -> DwgRecord:
    Fields: list[DwgField] = []
    Position = 0
    while Position < len(DataValue):
        ItemCode = DataValue[Position]
        Value, Position = ReadEedValue(DataValue, Position + 1, ItemCode)
        Fields.append(DwgField(str(1000 + ItemCode), Value))
    return DwgRecord(tuple(Fields))


def EncodeEedValue(ItemCode: int, Value: KDwgValue) -> bytes:
    if ItemCode == 0:
        Encoded = AsText(Value).encode("utf-16-le")
        return PackFields("<H", len(Encoded) // 2) + Encoded
    if ItemCode in (3, 5):
        return AsBytes(Value)
    if ItemCode == 4:
        return bytes((len(AsBytes(Value)),)) + AsBytes(Value)
    if 10 <= ItemCode <= 13:
        return PackFields("<3d", *AsPoint(Value, 3))
    Layout = KFixedSizes.get(ItemCode)
    if Layout is None:
        raise ValueError(f"DWG extended data item code {ItemCode} is unsupported")
    if Layout == "<d":
        return PackFields(Layout, AsFloat(Value))
    return PackFields(Layout, AsInt(Value))


def EncodeEedItems(EedItems: DwgRecord) -> bytes:
    return b"".join(
        bytes((int(Entry.FieldName) - 1000,))
        + EncodeEedValue(int(Entry.FieldName) - 1000, Entry.FieldValue)
        for Entry in EedItems.RecordFields
    )
