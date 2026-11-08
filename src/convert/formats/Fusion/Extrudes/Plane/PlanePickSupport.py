# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.PickSupport import KSupportGuid

# the fixed selection helper separates typed links from an opaque cached scalar
KPlanePickHelper = "5FBE538E-139B-46D4-BCAF-CC796D1E1F78"


# identical trailer framing preserves exact reciprocal links in both selector roles
def ReadPickFooter(
    BulkData: bytes, Owners: dict[int, RecordSpan], Cursor: MetaCursor
) -> tuple[int, int]:
    if (
        Cursor.ReadWord() != 0
        or Cursor.ReadWord() != 5
        or Cursor.TakeBytes(10) != bytes(10)
        or Cursor.TakeBytes(4) != b"\1\1\0\0"
    ):
        raise ValueError("Unsupported Fusion plane selection trailer")
    Cursor.TakeBytes(8)
    if Cursor.TakeBytes(4) != b"\1\1\0\0":
        raise ValueError("Unsupported Fusion plane selection trailer marker")
    HelperId = ReadNativeRef(Cursor)
    Helper = SelectCursor(BulkData, Owners, HelperId, KPlanePickHelper)
    if Helper.DataValue != b"\0\1" + bytes(12) or Cursor.TakeBytes(3) != b"\1\0\0":
        raise ValueError("Unsupported Fusion plane selection helper")
    SupportId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion plane selection support marker")
    return HelperId, SupportId


# ordered supports and repeated ownership corroborate the selected plane creator
def CheckPickLinks(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SupportId: int,
    PickId: int,
    Expected: tuple[int, ...],
) -> None:
    Cursor = SelectCursor(BulkData, Owners, SupportId, KSupportGuid)
    if (
        Cursor.TakeBytes(8) != bytes(6) + b"\1\1"
        or Cursor.ReadWord() != len(Expected)
        or len(Cursor.DataValue) != 39 + 19 * len(Expected)
    ):
        raise ValueError("Unsupported Fusion plane selection support framing")
    for Identity in Expected:
        if ReadNativeRef(Cursor) != Identity:
            raise ValueError("Fusion plane selection support members disagree")
        Cursor.ReadLong()
    if ReadNativeRef(Cursor) != PickId:
        raise ValueError("Fusion plane selection support owner disagrees")
    Cursor.ReadLong()
    if Cursor.TakeBytes(8) != bytes(8):
        raise ValueError("Unsupported Fusion plane selection support suffix")
