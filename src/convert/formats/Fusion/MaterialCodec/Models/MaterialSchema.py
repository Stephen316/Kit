from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec


@MakeDataClass(frozen=True, slots=True)
class MaterialSchema:
    SchemaName: str
    Bases: tuple[str, ...]
    Properties: tuple[PropertySpec, ...]
