# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor


# suppression is projected only when the shared native footer proves both copies
def ReadFeatState(BodyValue: bytes) -> tuple[bool, bool] | None:
    TailValue = BodyValue[-66:]
    if (
        len(TailValue) != 66
        or TailValue[:5] != bytes(5)
        or TailValue[5] not in (0, 1)
        or TailValue[6] != 0
        or TailValue[18] != 0
        or TailValue[23:27] != b"\1\1\0\0"
        or TailValue[35:39] != b"\1\1\0\0"
        or TailValue[50] != 1
        or TailValue[51] != TailValue[5]
        or TailValue[52] not in (0, 1)
        or TailValue[64:] != bytes(2)
    ):
        return None
    Cursor = MetaCursor(TailValue)
    try:
        for Offset in (7, 39, 53):
            Cursor.Offset = Offset
            _ = ReadNativeRef(Cursor)
    except ValueError:
        return None
    return bool(TailValue[5]), bool(TailValue[52])
