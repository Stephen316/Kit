from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class QualifierValue:
    ImagePath: str | None
