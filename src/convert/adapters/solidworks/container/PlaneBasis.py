from itertools import combinations as Combinations
from math import isclose as IsClose, sqrt as SquareRoot
from typing import TypeAlias

from convert.adapters.solidworks.container.Archive import ArchiveError

# saved planar orientations are three spatial coordinates per axis
KSavedVector: TypeAlias = tuple[float, float, float]

# orientation proof needs a complete basis rather than only a plane normal
KSavedBasis: TypeAlias = tuple[KSavedVector, KSavedVector, KSavedVector]

# an omitted matrix in a native transform represents this coordinate frame
KUnitRows = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# both sketch readers must interpret saved column axes in the same order
def MatrixAxes(RowsValue: tuple[float, ...]) -> KSavedBasis:
    if len(RowsValue) != 9:
        raise ArchiveError("SOLIDWORKS basis requires nine matrix scalars")
    return (
        (RowsValue[0], RowsValue[3], RowsValue[6]),
        (RowsValue[1], RowsValue[4], RowsValue[7]),
        (RowsValue[2], RowsValue[5], RowsValue[8]),
    )


# malformed vectors need a common refusal before either sketch path expands its coordinates
def IsOrthonormal(Vectors: tuple[KSavedVector, ...]) -> bool:
    return all(
        IsClose(SquareRoot(sum(Value * Value for Value in Vector)), 1.0, abs_tol=1e-9)
        for Vector in Vectors
    ) and all(
        IsClose(
            sum(
                First * Second
                for First, Second in zip(LeftValue, RightValue, strict=True)
            ),
            0.0,
            abs_tol=1e-9,
        )
        for LeftValue, RightValue in Combinations(Vectors, 2)
    )
