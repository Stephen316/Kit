# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose
from struct import pack as Pack, unpack_from as UnpackFrom

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.PlaneAxes import ReadPlaneAxes
from interchange.geometry.models.Transform import Transform


# native matrices store component placement in centimetres with basis columns
def ReadFrame(BodyValue: bytes) -> tuple[Transform, int]:
    if (
        BodyValue[:2] != bytes(2)
        or len(BodyValue) not in (15, 143)
        or BodyValue[-12] != 0
    ):
        raise ValueError("Unsupported Fusion sketch transform framing")
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = len(BodyValue) - 11
    ComponentId = ReadNativeRef(Cursor)
    if BodyValue[:4] == b"\0\0\1\0" and len(BodyValue) == 15:
        return Transform(), ComponentId
    if BodyValue[2] != 0 or len(BodyValue) != 143:
        raise ValueError("Unsupported Fusion sketch transform encoding")
    Values = tuple(float(Value) for Value in UnpackFrom("<16d", BodyValue, 3))
    if any(
        not IsClose(Value, Target, abs_tol=1e-9)
        for Value, Target in zip(Values[12:], (0.0, 0.0, 0.0, 1.0))
    ):
        raise ValueError("Non-affine Fusion sketch transform")
    Frame = ReadPlaneAxes(
        Pack("<9d", *(Values[Index] for Index in (3, 7, 11, 0, 4, 8, 1, 5, 9)))
    )
    AxisZ = Frame.z_axis
    if any(
        not IsClose(Value, Target, abs_tol=1e-9)
        for Value, Target in zip((AxisZ.x, AxisZ.y, AxisZ.z), Values[2:12:4])
    ):
        raise ValueError("Fusion sketch transform normal disagrees with its axes")
    return Frame, ComponentId
