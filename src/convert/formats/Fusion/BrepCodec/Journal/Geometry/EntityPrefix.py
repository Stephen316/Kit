from dataclasses import dataclass as MakeDataClass


# entity prefix needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class EntityPrefix:
    Attribute: int
    EntityTag: int
