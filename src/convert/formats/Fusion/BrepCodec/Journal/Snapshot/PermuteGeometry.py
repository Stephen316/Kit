from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.ShiftSubtypes import (
    ShiftSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckRootOrder import (
    CheckRootOrder,
)


def PermuteGeometry(Model: GeometryState, Order: tuple[int, ...]) -> GeometryState:
    CheckGeometry(Model)
    if type(Order) is not tuple or any(type(Value) is not int for Value in Order):
        raise ValueError(
            "Fusion geometry allocation requires immutable integer ordinals"
        )
    if (
        len(Order) != len(Model.Entities)
        or sorted(Order) != list(range(len(Order)))
        or Order[0] != 0
    ):
        raise ValueError("Invalid Fusion geometry permutation or header placement")
    CheckRootOrder(Model.Entities, Order)
    Mapping = tuple(Order.index(Index) for Index in range(len(Order)))
    Shifted = ShiftSubtypes(Model.Entities, Order)
    Result = ReplaceValue(
        Model,
        Entities=tuple(RemapEntity(Shifted[Index], Mapping) for Index in Order),
    )
    CheckGeometry(Result)
    return Result
