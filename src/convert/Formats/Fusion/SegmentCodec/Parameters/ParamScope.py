from dataclasses import dataclass as MakeDataClass


# parameter scope needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class ParamScope:
    CollectionId: int
    RegistryId: int
    ComponentId: int
    HighWaterMark: int
    MemberIds: tuple[int, ...]
    NameRows: tuple[tuple[int, str], ...]
