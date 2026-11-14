from struct import pack as PackValue
from struct import unpack_from as UnpackFrom
from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.DrawingCodec.Members.FreezeJson import FreezeJson
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson


def EmitProperties(Value: JsonFields) -> bytes:
    if not isinstance(CastValue(object, Value), JsonFields):
        raise ValueError("Fusion drawing properties must be a JSON object")
    TextValue = WriteJson(Value, JsonStyle.KCompact)
    return PackValue("<I", len(TextValue)) + TextValue


def ReadProperties(Payload: bytes) -> JsonFields:
    if len(Payload) < 4 or UnpackFrom("<I", Payload)[0] != len(Payload) - 4:
        raise ValueError("Invalid Fusion drawing properties length")
    Value = FreezeJson(ReadJson(Payload[4:]))
    if not isinstance(Value, JsonFields) or EmitProperties(Value) != Payload:
        raise ValueError("Fusion drawing properties are not canonical")
    return Value
