# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.Cylinder.CylinderFrame import CylinderGap
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan


# opposite rim traversals and generator stations close one bounded periodic rectangle
def IsCylinderQuad(
    Spans: tuple[CylinderSpan, ...], Allowed: float, AngleTol: float
) -> bool:
    if Spans[0].Sweep == 0.0:
        Spans = Spans[1:] + Spans[:1]
    First, Right, Second, LeftValue = Spans
    if (
        First.Sweep == 0.0
        or Second.Sweep == 0.0
        or Right.Sweep != 0.0
        or LeftValue.Sweep != 0.0
    ):
        return False
    if (
        (First.Sweep > 0.0) == (Second.Sweep > 0.0)
        or abs(First.Sweep + Second.Sweep) > AngleTol
        or not abs(First.StartStation - Second.StartStation) > Allowed
        or (Right.EndStation > Right.StartStation)
        == (LeftValue.EndStation > LeftValue.StartStation)
    ):
        return False
    return all(
        abs(Current.EndStation - Following.StartStation) <= Allowed
        and CylinderGap(Current.EndRadial, Following.StartRadial) <= Allowed
        for Current, Following in zip(Spans, Spans[1:] + Spans[:1])
    )
