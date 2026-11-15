from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder


# uv order entry needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class UvOrderEntry:
    KeyValue: int
    Value: UvOrder
