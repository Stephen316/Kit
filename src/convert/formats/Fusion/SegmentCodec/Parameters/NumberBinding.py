from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class NumberBinding:
    OwnerId: int
    ParamId: int
    BookId: int
    ObserverIndex: int
    RuntimeParamId: int
    Number: float
