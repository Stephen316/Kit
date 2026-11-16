from dataclasses import dataclass as MakeDataClass


# the reference operation needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class CrossRef:
    ObjectId: int
    Token: int
    TypeGuid: str
