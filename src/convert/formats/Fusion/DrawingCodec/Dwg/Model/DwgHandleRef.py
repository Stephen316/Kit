from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgHandleRef:
    RefCode: int
    RefValue: int
