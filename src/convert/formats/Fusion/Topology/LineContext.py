# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import hypot as Hypot, isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# the linear witness stores its first point and an oriented displacement
KLineContext = "50AEE8B4-9456-4DD7-847D-6F6C909BBB9D"


# preserve the stored line direction independently of sweep orientation
def ReadLineCtx(
    BulkData: bytes, Owners: dict[int, RecordSpan], ContextId: int
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    Cursor = SelectCursor(BulkData, Owners, ContextId, KLineContext)
    if len(Cursor.DataValue) != 55 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion topology line context layout")
    Values = Unpack("<6d", Cursor.TakeBytes(48))
    if Cursor.TakeBytes(5) != b"\0\0\0\1\0":
        raise ValueError("Unsupported Fusion topology line context suffix")
    Start, Delta = Values[:3], Values[3:]
    EndValue = tuple(First + Change for First, Change in zip(Start, Delta))
    Length = Hypot(*Delta)
    if not all(map(IsFinite, Values + EndValue + (Length,))) or Length <= 1e-12:
        raise ValueError("Degenerate Fusion topology line context")
    return Start, EndValue
