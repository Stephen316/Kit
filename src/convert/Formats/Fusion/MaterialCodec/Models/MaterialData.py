from dataclasses import dataclass as MakeDataClass


# material data needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class MaterialData:
    TableData: bytes
    DefinitionData: bytes
    InstanceData: bytes
