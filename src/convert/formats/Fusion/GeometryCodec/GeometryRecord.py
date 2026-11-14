from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


@MakeDataClass(frozen=True, slots=True)
class GeometryRecord:
    NameValue: str
    Fields: tuple[KGeometryValue, ...]
