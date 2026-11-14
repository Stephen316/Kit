from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AttribLinks:
    NextAttrib: int
    PriorAttrib: int
    OwnerRef: int
