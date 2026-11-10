# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# both instance forms use the same role and reference fields after the root name
def ReadActInstLink(Cursor: MetaCursor, Identity: int) -> int:
    if Cursor.ReadText(Maximum=15) not in ("ACTInstanceRoot", ""):
        raise ValueError("Unsupported Fusion ACT route instance name")
    if Cursor.TakeBytes(3) != bytes(3) or Cursor.ReadCount(6) != len(ActRole):
        raise ValueError("Unsupported Fusion ACT route instance prefix")
    if tuple(Cursor.ReadText(Maximum=16) for _ in ActRole) != tuple(ActRole):
        raise ValueError("Fusion ACT route instance roles disagree")
    if (
        Cursor.TakeBytes(1) != b"\0"
        or ReadNativeRef(Cursor) != Identity
        or Cursor.TakeBytes(1) != b"\0"
    ):
        raise ValueError("Fusion ACT route instance identity disagrees")
    return ReadNativeRef(Cursor)
