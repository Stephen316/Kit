from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


@MakeDataClass(frozen=True, slots=True)
class NativeSchema:
    NameValue: str
    ClassSpace: str
    Value: ClassSchema
