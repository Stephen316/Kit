from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class DrawingDatabase:
    FileName: str
    Content: bytes
