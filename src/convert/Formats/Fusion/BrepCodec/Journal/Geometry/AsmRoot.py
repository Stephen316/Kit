from dataclasses import dataclass as MakeDataClass


# asm root needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class AsmRoot:
    Attribute: int
    EntityTag: int
    KernelVersion: str
