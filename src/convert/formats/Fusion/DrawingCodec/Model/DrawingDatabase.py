from dataclasses import dataclass as MakeDataClass


# drawing database needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingDatabase:
    FileName: str
    Content: bytes
