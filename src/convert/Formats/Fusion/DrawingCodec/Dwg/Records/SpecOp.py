from dataclasses import dataclass as MakeDataClass


# specification op needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class SpecOp:
    OpKind: str
    OpName: str
    OpArgs: tuple[str, ...]
    BodyOps: tuple["SpecOp", ...]
    ElseOps: tuple["SpecOp", ...]
