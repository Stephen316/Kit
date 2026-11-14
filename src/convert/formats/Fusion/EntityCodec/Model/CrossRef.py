from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class CrossRef:
    ObjectId: int
    Token: int
    TypeGuid: str
