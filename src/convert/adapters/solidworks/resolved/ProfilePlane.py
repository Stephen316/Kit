from math import isclose as IsClose

from convert.adapters.solidworks.container.Archive import KClassRefKind
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.PlaneBasis import (
    KSavedBasis,
    KUnitRows,
    IsOrthonormal,
    MatrixAxes,
)
from convert.adapters.solidworks.resolved.PrincipalRef import PrincipalRef, ReadPlaneRef


# optional kernel and edge structures select the native local principal reference branch
def ReadProfileRef(Cursor: ArchiveCursor, Generation: int) -> PrincipalRef:
    RequireArch(Cursor.ReadInts("<iB"), (3, 1), "absent rectangle kernel packet")
    RequireArch(Cursor.ReadInts("<iHI"), (0, 0, 0), "empty rectangle edge tables")
    RequireArch(Cursor.ReadInts("<IH"), (100000, 0), "empty rectangle contour map")
    Cursor.ReadNull()
    return ReadPlaneRef(Cursor, Generation, KClassRefKind)


# a matching owner and a matching frame are both required for principal sketch placement
def CheckProfileRef(
    Reference: PrincipalRef,
    DatumPoint: tuple[float, ...],
    DatumNormal: tuple[float, ...],
) -> KSavedBasis:
    AxisCode = Reference.AxisCode
    RequireArch(AxisCode in (1, 3), True, "witnessed principal support axes")
    RequireArch(
        DatumNormal[AxisCode - 1], 1.0, "principal support axis agrees with its plane"
    )
    SavedAxes = MatrixAxes(
        Reference.BasisValue if Reference.BasisValue is not None else KUnitRows
    )
    RequireArch(IsOrthonormal(SavedAxes), True, "orthonormal sketch frame")
    (XFirst, XSecond, XThird), (YFirst, YSecond, YThird), Normal = SavedAxes
    Cross = (
        XSecond * YThird - XThird * YSecond,
        XThird * YFirst - XFirst * YThird,
        XFirst * YSecond - XSecond * YFirst,
    )
    RequireArch(
        all(
            IsClose(Expected, Actual, abs_tol=1e-9)
            for Expected, Actual in zip(Normal, Cross, strict=True)
        ),
        True,
        "right-handed sketch frame",
    )
    RequireArch(Normal, DatumNormal, "saved sketch normal agrees with its plane")
    RequireArch(
        Reference.ShiftScale,
        (*DatumPoint, 1.0),
        "saved sketch origin and scale agree with its plane",
    )
    return SavedAxes
