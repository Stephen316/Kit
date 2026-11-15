from dataclasses import dataclass as MakeDataClass


# asset entry needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class AssetEntry:
    InstanceId: str
    AssetRole: str
    DefinitionRoot: int
    InstanceRoot: int
    SchemaName: str
