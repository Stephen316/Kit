from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass
from dataclasses import field as DataField

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Values.ValueQuota import ValueQuota


@MakeDataClass(frozen=True, slots=True)
class EntityCatalog:
    RootGuid: str
    Classes: Mapping[str, ClassSchema]
    LocalClasses: Mapping[int, str]
    ExternalClasses: Mapping[tuple[int, int], str]
    NamedTypes: Mapping[str, WireType]
    Quota: ValueQuota = DataField(default_factory=ValueQuota)
