from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CountedText:
    Value: str
