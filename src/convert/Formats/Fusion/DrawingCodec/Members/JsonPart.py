from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Members.JsonFields import KFrozenJson
from convert.Formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle


# json part needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class JsonPart:
    Name: str
    Value: KFrozenJson
    Style: JsonStyle
