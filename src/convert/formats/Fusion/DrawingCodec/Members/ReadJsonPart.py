from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.DrawingCodec.Members.FreezeJson import FreezeJson
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson


def ReadJsonPart(NameValue: str, Payload: bytes) -> JsonPart:
    Value = FreezeJson(ReadJson(Payload))
    for Style in JsonStyle:
        if WriteJson(Value, Style) == Payload:
            return JsonPart(NameValue, Value, Style)
    raise ValueError("Unsupported Fusion drawing JSON formatting")
