from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# geometry record needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class GeometryRecord:
    NameValue: str
    Fields: tuple[KGeometryValue, ...]
