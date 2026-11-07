# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    XX, XY, XZ = XAxis
    YX, YY, YZ = YAxis
    Cross = (XY * YZ - XZ * YY, XZ * YX - XX * YZ, XX * YY - XY * YX)
    if any(
        not IsClose(sum(Value * Value for Value in Axis), 1.0, abs_tol=1e-9)
        for Axis in (XAxis, YAxis, ZAxis)
    ) or any(
        not IsClose(Actual, Expected, abs_tol=1e-9)
        for Actual, Expected in zip(Cross, ZAxis)
    ):
        raise ValueError("Non-rigid Fusion occurrence transform")
    return Matrix
