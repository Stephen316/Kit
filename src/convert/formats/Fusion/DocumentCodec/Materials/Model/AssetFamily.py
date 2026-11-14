from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue


@MakeDataClass(frozen=True, slots=True)
class AssetFamily:
    SchemaName: str
    InstanceId: str
    DefinitionId: str
    AssetRole: str
    NameValue: str
    Properties: tuple[PropertyValue, ...] = ()
