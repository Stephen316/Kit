from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AssetEntry:
    InstanceId: str
    AssetRole: str
    DefinitionRoot: int
    InstanceRoot: int
    SchemaName: str
