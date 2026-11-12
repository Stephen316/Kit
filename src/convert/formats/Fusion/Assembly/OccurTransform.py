from math import isclose as IsClose, isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.MetaCursor import MetaCursor

# compact transform records represent exact identity placement
KIdentityMatrix = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


# reject transforms outside the verified right handed rigid assembly scope
def ReadOccurMatrix(Cursor: MetaCursor) -> tuple[float, ...]:
    TransformFlag = Cursor.TakeBytes(1)
    if TransformFlag == b"\1":
        return KIdentityMatrix
    if TransformFlag != bytes(1):
        raise ValueError("Unsupported Fusion occurrence transform flag")
    Matrix = Unpack("<16d", Cursor.TakeBytes(128))
    if (
        not all(map(IsFinite, Matrix))
        or Matrix[12:] != KIdentityMatrix[12:]
        or not all(IsFinite(Matrix[Index] * 10) for Index in (3, 7, 11))
    ):
        raise ValueError("Invalid Fusion occurrence affine transform")
    XAxis, YAxis, ZAxis = (Matrix[Column:12:4] for Column in range(3))
    EntryXX, EntryXY, EntryXZ = XAxis
    EntryYX, EntryYY, EntryYZ = YAxis
    Cross = (
        EntryXY * EntryYZ - EntryXZ * EntryYY,
        EntryXZ * EntryYX - EntryXX * EntryYZ,
        EntryXX * EntryYY - EntryXY * EntryYX,
    )
    if any(
        not IsClose(sum(Value * Value for Value in AxisValue), 1.0, abs_tol=1e-9)
        for AxisValue in (XAxis, YAxis, ZAxis)
    ) or any(
        not IsClose(Actual, Expected, abs_tol=1e-9)
        for Actual, Expected in zip(Cross, ZAxis)
    ):
        raise ValueError("Non-rigid Fusion occurrence transform")
    return Matrix
