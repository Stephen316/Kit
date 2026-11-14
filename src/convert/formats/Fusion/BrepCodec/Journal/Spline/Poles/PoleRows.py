from typing import Iterable as KIterable

KPoleRow = dict[int, float]
KFrozenRow = tuple[tuple[int, float], ...]
KIndexedRow = tuple[int | None, KPoleRow]


def MixRows(Parts: KIterable[tuple[float, KPoleRow]]) -> KPoleRow:
    Total: KPoleRow = {}
    for Scalar, RowValue in Parts:
        if Scalar == 0.0:
            continue
        for GripIndex, Value in RowValue.items():
            Total[GripIndex] = Total.get(GripIndex, 0.0) + Scalar * Value
    return Total


def FreezeRow(RowValue: KPoleRow) -> KFrozenRow:
    return tuple(
        (GripIndex, Value)
        for GripIndex, Value in sorted(RowValue.items())
        if Value != 0.0
    )


def BlendRows(Lower: KIndexedRow, Upper: KIndexedRow, Alpha: float) -> KIndexedRow:
    if Alpha == 0.0:
        return Lower
    if Alpha == 1.0:
        return Upper
    return (None, MixRows(((1.0 - Alpha, Lower[1]), (Alpha, Upper[1]))))
