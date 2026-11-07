# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.MetaCursor import MetaCursor


# typed geometry properties bound the payload offset without scanning for byte patterns
def ReadGeomAttrs(Cursor: MetaCursor) -> dict[str, int | float]:
    if Cursor.TakeBytes(2) != b"\0\1":
        raise ValueError("Unsupported Fusion sketch geometry prefix")
    Values: dict[str, int | float] = {}
    for _ in range(Cursor.ReadCount(32)):
        NameValue = Cursor.ReadText(Maximum=256)
        KindValue = Cursor.ReadText(Maximum=256)
        if not NameValue or NameValue in Values:
            raise ValueError("Invalid Fusion sketch geometry attribute")
        if KindValue == "IntrinsicMetaTypeuint64":
            Values[NameValue] = Cursor.ReadLong()
        elif KindValue == "IntrinsicMetaTypedouble":
            Number = float(Unpack("<d", Cursor.TakeBytes(8))[0])
            if not IsFinite(Number):
                raise ValueError("Non-finite Fusion sketch geometry attribute")
            Values[NameValue] = Number
        else:
            raise ValueError("Unsupported Fusion sketch geometry attribute type")
    return Values
