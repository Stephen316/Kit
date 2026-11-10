# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Extrudes.ExtrudeControl import ReadExtControls
from convert.formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadSelectUuid
from convert.formats.Fusion.Topology.BodyAnchor import KAnchorGuid


# an earlier body remains selectable even when its creator anchor is no longer active
def CheckExtAnchor(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    AnchorId: int,
    ResultOffset: int | None = None,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    if ResultOffset is None:
        Fields = ReadExtControls(Cursor)
        _ = ReadExtProfile(BulkData, Owners, Cursor, FeatureId, Fields.SideMode)
    else:
        Cursor.Offset = ResultOffset
    if (
        Cursor.TakeBytes(4) != bytes(4)
        or Cursor.ReadWord() != 1
        or ReadNativeRef(Cursor) != AnchorId
        or Cursor.TakeBytes(8) != bytes(8)
    ):
        raise ValueError("Fusion Extrude result anchor does not match the creator")
    _ = ReadSelectUuid(Cursor)


# final geometry requires a reciprocal creator link and an active result anchor
def CheckExtResult(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    AnchorId: int,
    ResultOffset: int | None = None,
) -> None:
    CheckExtAnchor(BulkData, Owners, FeatureId, AnchorId, ResultOffset)
    Anchor = SelectCursor(BulkData, Owners, AnchorId, KAnchorGuid)
    if Anchor.DataValue[78:80] != b"\0\1":
        raise ValueError("Fusion Extrude result anchor is inactive or unverified")
