from dataclasses import dataclass as MakeDataClass


# attribute links needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class AttribLinks:
    NextAttrib: int
    PriorAttrib: int
    OwnerRef: int
