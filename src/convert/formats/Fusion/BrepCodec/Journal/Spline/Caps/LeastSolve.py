import math
from sys import float_info as FloatInfo

KRankSlack = 1e-9
KUnitRound = FloatInfo.epsilon


def ColumnNorm(Column: list[float], Start: int) -> float:
    return math.fsum(Value * Value for Value in Column[Start:])


def ReflectMut(Vector: list[float], Column: list[float], Start: int) -> None:
    Denom = math.fsum(Value * Value for Value in Vector)
    if Denom == 0.0:
        return
    Inner = math.fsum(
        LeftValue * RightValue for LeftValue, RightValue in zip(Vector, Column[Start:])
    )
    Factor = 2.0 * Inner / Denom
    if Factor == 0.0:
        return
    for Offset, Value in enumerate(Vector):
        Column[Start + Offset] -= Factor * Value


def BackSolve(Columns: list[list[float]], Target: list[float]) -> list[float]:
    Count = len(Columns)
    Found = [0.0] * Count
    for RowIndex in range(Count - 1, -1, -1):
        Total = Target[RowIndex] - math.fsum(
            Columns[Later][RowIndex] * Found[Later]
            for Later in range(RowIndex + 1, Count)
        )
        Found[RowIndex] = Total / Columns[RowIndex][RowIndex]
    return Found


def PivotMut(Columns: list[list[float]], Order: list[int], Start: int) -> None:
    Pivot = max(
        range(Start, len(Columns)), key=lambda Index: ColumnNorm(Columns[Index], Start)
    )
    Columns[Start], Columns[Pivot] = Columns[Pivot], Columns[Start]
    Order[Start], Order[Pivot] = Order[Pivot], Order[Start]


def ReduceMut(
    Columns: list[list[float]], Targets: list[list[float]], Start: int, Leading: float
) -> float:
    Leader = Columns[Start]
    Alpha = math.sqrt(ColumnNorm(Leader, Start))
    Leading = Leading or Alpha
    if Start >= len(Leader) or Alpha <= KRankSlack * Leading:
        raise ValueError(
            "Fusion Form cap rule leaves "
            + str(len(Columns) - Start)
            + " free directions"
        )
    if Leader[Start] > 0.0:
        Alpha = -Alpha
    Vector = Leader[Start:]
    Vector[0] -= Alpha
    for Column in Columns[Start + 1 :] + Targets:
        ReflectMut(Vector, Column, Start)
    Leader[Start] = Alpha
    for RowIndex in range(Start + 1, len(Leader)):
        Leader[RowIndex] = 0.0
    return Leading


def RoundFloor(Columns: list[list[float]], Found: list[list[float]]) -> float:
    Diagonal = [abs(Column[Index]) for Index, Column in enumerate(Columns)]
    Largest = max((abs(Value) for RowValue in Found for Value in RowValue), default=0.0)
    return KUnitRound * len(Columns[0]) * max(Diagonal) / min(Diagonal) * Largest


def SolveLeast(
    Matrix: list[list[float]], Sides: list[list[float]]
) -> list[list[float]]:
    Width = len(Matrix[0])
    Depth = len(Sides[0])
    Columns = [[RowValue[Column] for RowValue in Matrix] for Column in range(Width)]
    Targets = [[RowValue[Column] for RowValue in Sides] for Column in range(Depth)]
    Order = list(range(Width))
    Leading = 0.0
    for Start in range(Width):
        PivotMut(Columns, Order, Start)
        Leading = ReduceMut(Columns, Targets, Start, Leading)
    Solved = [BackSolve(Columns, Target) for Target in Targets]
    Found = [[0.0] * Depth for _ in range(Width)]
    for Start, Column in enumerate(Order):
        for Index in range(Depth):
            Found[Column][Index] = Solved[Index][Start]
    Floor = RoundFloor(Columns, Found)
    return [
        [Value if abs(Value) > Floor else 0.0 for Value in RowValue]
        for RowValue in Found
    ]
