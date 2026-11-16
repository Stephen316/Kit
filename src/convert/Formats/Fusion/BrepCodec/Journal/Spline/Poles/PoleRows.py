from typing import Iterable as KIterable

# the pole row shape must stay shared so spline pole reconstruction uses one contract for compatible values
KPoleRow = dict[int, float]

# the frozen row shape must stay shared so spline pole reconstruction uses one contract for compatible values
KFrozenRow = tuple[tuple[int, float], ...]

# the indexed row shape must stay shared so spline pole reconstruction uses one contract for compatible values
KIndexedRow = tuple[int | None, KPoleRow]


# the rows operation needs one geometric convention so neighboring patches retain consistent subdivision boundaries
def MixRows(Parts: KIterable[tuple[float, KPoleRow]]) -> KPoleRow:
    Total: KPoleRow = {}
    for Scalar, RowValue in Parts:
        if Scalar == 0.0:
            continue
        for GripIndex, Value in RowValue.items():
            Total[GripIndex] = Total.get(GripIndex, 0.0) + Scalar * Value
    return Total


# the freeze row contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def FreezeRow(RowValue: KPoleRow) -> KFrozenRow:
    return tuple(
        (GripIndex, Value)
        for GripIndex, Value in sorted(RowValue.items())
        if Value != 0.0
    )


# the rows operation needs one geometric convention so neighboring patches retain consistent subdivision boundaries
def BlendRows(Lower: KIndexedRow, Upper: KIndexedRow, Alpha: float) -> KIndexedRow:
    if Alpha == 0.0:
        return Lower
    if Alpha == 1.0:
        return Upper
    return (None, MixRows(((1.0 - Alpha, Lower[1]), (Alpha, Upper[1]))))
