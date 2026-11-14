from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder


@MakeDataClass(frozen=True, slots=True)
class UvOrderEntry:
    KeyValue: int
    Value: UvOrder
