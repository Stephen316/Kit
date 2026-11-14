from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SubtypeRef:
    Family: str
    Index: int
