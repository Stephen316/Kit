# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from sys import float_info as FloatInfo

# shared side names keep reference roles and evaluated distances in agreement
KDistModes = ("one_sided", "two_sided", "symmetric_full", "symmetric_half")


# signed profile relative bounds retain the effect of offsets and reversed distances
def GetDistSpan(
    AlongMm: float, AgainstMm: float | None, OffsetMm: float, SideMode: str
) -> tuple[float, float]:
    Controls = (
        (AlongMm, OffsetMm) if AgainstMm is None else (AlongMm, OffsetMm, AgainstMm)
    )
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in Controls
    ):
        raise ValueError("distance extrusion requires finite axial controls")
    AlongMm, OffsetMm = float(AlongMm), float(OffsetMm)
    AgainstMm = None if AgainstMm is None else float(AgainstMm)
    if SideMode not in KDistModes:
        raise ValueError("distance extrusion has an invalid side mode")
    if (SideMode == "two_sided") != (AgainstMm is not None):
        raise ValueError("distance extrusion side mode and against distance disagree")
    if SideMode == "one_sided":
        Lower = min(OffsetMm, OffsetMm + AlongMm)
        Upper = max(OffsetMm, OffsetMm + AlongMm)
    elif AlongMm <= 0.0 or (AgainstMm is not None and AgainstMm <= 0.0):
        raise ValueError("two sided and symmetric extrusion distances must be positive")
    elif AgainstMm is not None:
        Lower, Upper = OffsetMm - AgainstMm, OffsetMm + AlongMm
    else:
        HalfSpan = AlongMm / 2.0 if SideMode == "symmetric_full" else AlongMm
        Lower, Upper = OffsetMm - HalfSpan, OffsetMm + HalfSpan
    if not (
        IsFinite(Lower)
        and IsFinite(Upper)
        and Lower < Upper
        and IsFinite(Upper - Lower)
    ):
        raise ValueError("distance extrusion requires finite distinct axial limits")
    return Lower, Upper
