from math import isfinite as IsFinite
from typing import cast as CastValue

KRigidTolerance = 1e-9


def ComposeMatrix(
    LeftValue: tuple[float, ...], RightValue: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(
        sum(
            LeftValue[RowIndex * 4 + Inner] * RightValue[Inner * 4 + Column]
            for Inner in range(4)
        )
        for RowIndex in range(4)
        for Column in range(4)
    )


def InvertRigid(Matrix: tuple[float, ...]) -> tuple[float, ...]:
    Rotation = tuple(
        Matrix[Column * 4 + RowIndex] for RowIndex in range(3) for Column in range(3)
    )
    Offset = tuple(
        -sum(
            Rotation[RowIndex * 3 + Inner] * Matrix[Inner * 4 + 3] for Inner in range(3)
        )
        for RowIndex in range(3)
    )
    return (
        *Rotation[0:3],
        Offset[0],
        *Rotation[3:6],
        Offset[1],
        *Rotation[6:9],
        Offset[2],
        0.0,
        0.0,
        0.0,
        1.0,
    )


def IsFiniteNum(Entry: object) -> bool:
    return type(Entry) in (int, float) and IsFinite(CastValue(float, Entry))


def MatrixItems(Matrix: object) -> tuple[float, ...]:
    if type(Matrix) is not tuple:
        raise ValueError("Fusion placement matrix must be a tuple")
    Entries = CastValue(tuple[object, ...], Matrix)
    if len(Entries) != 16 or not all(IsFiniteNum(Entry) for Entry in Entries):
        raise ValueError("Fusion placement matrix must have 16 finite numbers")
    return tuple(float(CastValue(float, Entry)) for Entry in Entries)


def CheckMatrix(Matrix: object) -> tuple[float, ...]:
    Values = MatrixItems(Matrix)
    if Values[12:16] != (0.0, 0.0, 0.0, 1.0):
        raise ValueError("Fusion placement matrix must have an affine last row")
    Product = ComposeMatrix(InvertRigid(Values), Values)
    Identity = tuple(1.0 if Index % 5 == 0 else 0.0 for Index in range(16))
    if any(
        abs(First - Second) > KRigidTolerance
        for First, Second in zip(Product, Identity)
    ):
        raise ValueError("Fusion placement matrix must be a rigid transform")
    Determinant = (
        Values[0] * (Values[5] * Values[10] - Values[6] * Values[9])
        - Values[1] * (Values[4] * Values[10] - Values[6] * Values[8])
        + Values[2] * (Values[4] * Values[9] - Values[5] * Values[8])
    )
    if abs(Determinant - 1.0) > KRigidTolerance:
        raise ValueError("Fusion placement matrix must keep orientation")
    return Values
