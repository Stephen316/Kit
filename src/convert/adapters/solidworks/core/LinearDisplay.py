from dataclasses import dataclass as DataClass


# source formatting needs a representation separate from canonical physical units
@DataClass(frozen=True, slots=True)
class LinearDisplay:
    UnitName: str
    Decimals: int | None
