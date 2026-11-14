from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class MaterialData:
    TableData: bytes
    DefinitionData: bytes
    InstanceData: bytes
