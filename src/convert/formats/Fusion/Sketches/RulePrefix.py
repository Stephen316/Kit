# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs


# typed dependencies precede both geometric and dimensional relation payloads
def ReadRulePrefix(
    Cursor: MetaCursor,
) -> tuple[tuple[int, ...], tuple[int, ...], dict[str, int | float]]:
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion sketch relation dependency tag")
    Count = Cursor.ReadCount(16)
    if not Count:
        raise ValueError("Empty Fusion sketch relation dependency list")
    Identities: list[int]
    Slots: list[int]
    Identities, Slots = [], []
    for _ in range(Count):
        Identities.append(ReadNativeRef(Cursor))
        Slots.append(Cursor.ReadWord())
    return tuple(Identities), tuple(Slots), ReadGeomAttrs(Cursor, Prefix=b"\1")
