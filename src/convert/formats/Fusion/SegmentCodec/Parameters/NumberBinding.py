from dataclasses import dataclass as MakeDataClass


# number binding needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class NumberBinding:
    OwnerId: int
    ParamId: int
    BookId: int
    ObserverIndex: int
    RuntimeParamId: int
    Number: float
