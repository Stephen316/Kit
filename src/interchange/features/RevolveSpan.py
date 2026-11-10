# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isclose as IsClose
from math import tau as FullTurn
from sys import float_info as FloatInfo

# shared mode names keep editable references and sweep evaluation in agreement
KAngleModes = ("one_sided", "two_sided", "symmetric")


# angular limits retain directional intent and reject degenerate or excessive sweeps
def GetAngleSpan(
    Along: float, Against: float | None, SideMode: str
) -> tuple[float, float]:
    if SideMode not in KAngleModes:
        raise ValueError("angular revolution has an invalid side mode")
    Angles = (Along,) if Against is None else (Along, Against)
    if not all(
        type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
        for Value in Angles
    ):
        raise ValueError("angular revolution angles must be finite numbers")
    if SideMode == "one_sided":
        if Against is not None:
            raise ValueError(
                "one sided angular revolution cannot have an against angle"
            )
        Start, EndPoint = min(0.0, Along), max(0.0, Along)
    else:
        if Against is None or Against <= 0.0 or Along <= 0.0:
            raise ValueError(
                "two sided and symmetric angular revolution angles must be positive"
            )
        if SideMode == "symmetric" and not IsClose(
            Along, Against, abs_tol=1e-10, rel_tol=0.0
        ):
            raise ValueError("symmetric angular revolution angles must agree")
        Start, EndPoint = -Against, Along
    if not 1e-9 < EndPoint - Start <= FullTurn + 1e-10:
        raise ValueError(
            "angular revolution sweep must exceed tolerance and span at most one turn"
        )
    return float(Start), float(EndPoint)
