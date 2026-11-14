from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class FieldRule:
    FieldName: str
    WireKind: str
    ItemCount: int = 1
