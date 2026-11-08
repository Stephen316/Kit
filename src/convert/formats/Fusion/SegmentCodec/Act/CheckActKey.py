# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxWireId


# canonical route spelling keeps the same owner from having several native keys
def CheckActKey(KeyValue: str) -> None:
    if type(KeyValue) is not str or len(KeyValue) > 22:
        raise ValueError("Invalid Fusion ACT route key")
    Prefix, Marker, OwnerText = KeyValue.partition("_")
    if (
        Prefix not in ("0", "1", "3")
        or Marker != "_"
        or not OwnerText.isascii()
        or not OwnerText.isdecimal()
        or OwnerText.startswith("0")
        or int(OwnerText) > KMaxWireId
    ):
        raise ValueError("Invalid Fusion ACT route key")
