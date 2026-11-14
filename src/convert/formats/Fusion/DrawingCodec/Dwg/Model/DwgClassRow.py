from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgClassRow:
    ClassNumber: int
    ProxyFlags: int
    AppName: str
    CppName: str
    DxfName: str
    WasZombie: bool
    ItemClassId: int
    InstanceCount: int
    DwgVersion: int
    MaintVersion: int
    ReservedFirst: int
    ReservedSecond: int
