from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue


# asset family needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class AssetFamily:
    SchemaName: str
    InstanceId: str
    DefinitionId: str
    AssetRole: str
    NameValue: str
    Properties: tuple[PropertyValue, ...] = ()
