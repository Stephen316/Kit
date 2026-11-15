from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec


# material schema needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class MaterialSchema:
    SchemaName: str
    Bases: tuple[str, ...]
    Properties: tuple[PropertySpec, ...]
