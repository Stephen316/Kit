from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue


# material asset needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class MaterialAsset:
    SchemaName: str
    InstanceId: str
    DefinitionId: str
    AssetRole: str
    Definitions: tuple[PropertyValue, ...]
    Properties: tuple[PropertyValue, ...]
