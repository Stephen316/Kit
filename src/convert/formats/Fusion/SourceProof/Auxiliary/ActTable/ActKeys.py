# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# native record counts remain bounded independently of their declared widths
KMaxActKeys = 65536


# a native owner key cannot alias another segment or another spelling of an identity
def ReadActKeysMut(
    Cursor: MetaCursor,
) -> tuple[tuple[int, str, int, int], ...]:
    Entries: list[tuple[int, str, int, int]] = []
    LastKey = ""
    Count = Cursor.ReadCount(KMaxActKeys)
    if Count == 0:
        raise ValueError("Fusion ACT table has no field routes")
    for _ in range(Count):
        FieldsId = ReadNativeRef(Cursor)
        KeyValue = Cursor.ReadText(True, Maximum=22)
        Prefix, Marker, OwnerText = KeyValue.partition("_")
        if (
            KeyValue <= LastKey
            or Prefix not in ("0", "1", "3")
            or Marker != "_"
            or not OwnerText.isascii()
            or not OwnerText.isdecimal()
            or OwnerText.startswith("0")
            or (OwnerId := int(OwnerText)) >= 1 << 64
        ):
            raise ValueError("Invalid or unordered Fusion ACT route key")
        Entries.append((FieldsId, KeyValue, int(Prefix), OwnerId))
        LastKey = KeyValue
    return tuple(Entries)
