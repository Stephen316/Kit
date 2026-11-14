from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DwgAppEntry:
    KeyBytes: bytes
    TextValue: str
