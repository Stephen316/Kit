# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# named work points are scoped through a collection distinct from the origin
KPointList = "A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E"


# repeated local membership ties construction point geometry to its component
def CheckPointList(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    CollectionId: int,
    PointId: int,
    ComponentId: int,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KPointList)
    if (
        len(Cursor.DataValue) != 73
        or Cursor.TakeBytes(2) != bytes(2)
        or Cursor.ReadWord() != 1
        or ReadNativeRef(Cursor) != PointId
    ):
        raise ValueError("Unsupported Fusion construction point collection")
    Cursor.Offset = 47
    if (
        Cursor.ReadWord() != 1
        or ReadNativeRef(Cursor) != PointId
        or ReadNativeRef(Cursor) != ComponentId
    ):
        raise ValueError("Fusion construction point repeated collection disagrees")
