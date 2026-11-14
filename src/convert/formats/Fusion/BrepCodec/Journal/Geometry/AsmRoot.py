from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AsmRoot:
    Attribute: int
    EntityTag: int
    KernelVersion: str
