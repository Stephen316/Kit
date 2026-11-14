from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class ParamScope:
    CollectionId: int
    RegistryId: int
    ComponentId: int
    HighWaterMark: int
    MemberIds: tuple[int, ...]
    NameRows: tuple[tuple[int, str], ...]
