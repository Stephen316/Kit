from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


# native schema needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class NativeSchema:
    NameValue: str
    ClassSpace: str
    Value: ClassSchema
