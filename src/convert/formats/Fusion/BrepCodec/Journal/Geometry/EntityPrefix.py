from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class EntityPrefix:
    Attribute: int
    EntityTag: int
