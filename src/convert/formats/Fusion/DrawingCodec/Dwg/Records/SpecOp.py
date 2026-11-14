from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class SpecOp:
    OpKind: str
    OpName: str
    OpArgs: tuple[str, ...]
    BodyOps: tuple["SpecOp", ...]
    ElseOps: tuple["SpecOp", ...]
