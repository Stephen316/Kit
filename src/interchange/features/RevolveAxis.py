# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot
from math import isclose as IsClose
from sys import float_info as FloatInfo

from interchange.geometry.models.VectorSpace import SpaceVector


# shared axis qualification keeps every revolution definition safe for geometry consumers
def CheckRevAxis(AxisOrigin: SpaceVector, AxisDirection: SpaceVector) -> None:
    if not isinstance(AxisOrigin, SpaceVector) or not isinstance(
        AxisDirection, SpaceVector
    ):
        raise ValueError("revolution axis requires spatial vectors")
    Direction = (AxisDirection.x, AxisDirection.y, AxisDirection.z)
    Origin = (AxisOrigin.x, AxisOrigin.y, AxisOrigin.z)
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in (*Direction, *Origin)
    ):
        raise ValueError("revolution axis must contain finite numbers")
    if not IsClose(Hypot(*Direction), 1.0, abs_tol=1e-9, rel_tol=0.0):
        raise ValueError("revolution axis direction must have unit length")
