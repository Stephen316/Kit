from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Members.JsonFields import KFrozenJson
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle


@MakeDataClass(frozen=True, slots=True)
class JsonPart:
    Name: str
    Value: KFrozenJson
    Style: JsonStyle
