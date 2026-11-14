from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue


@MakeDataClass(frozen=True, slots=True)
class MaterialAsset:
    SchemaName: str
    InstanceId: str
    DefinitionId: str
    AssetRole: str
    Definitions: tuple[PropertyValue, ...]
    Properties: tuple[PropertyValue, ...]
