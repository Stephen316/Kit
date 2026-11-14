from dataclasses import dataclass as DataClass


@DataClass(frozen=True, slots=True)
class LinearDisplay:
    UnitName: str
    Decimals: int | None
