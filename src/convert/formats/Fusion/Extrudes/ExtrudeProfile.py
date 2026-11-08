# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Profiles.ProfileRef import (
    DescOwner,
    KLoopGuid,
    KProfileGuid,
    ReadProfileRef,
)
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectDesc, SelectCursor

# the sketch entity registry distinguishes sketch profile sources from arbitrary records
KExtrudeSketch = "44A64366-4BD3-4B24-881A-F94C206E8F2D"


# the wall boundary locates the owned proxy without guessing from nearby records
def ReadExtProfile(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Cursor: MetaCursor,
    FeatureId: int,
    SideMode: str,
) -> tuple[int, int]:
    WallWidth = 11 if SideMode.startswith("symmetric_") else 15
    if Cursor.TakeBytes(WallWidth) != bytes(WallWidth):
        raise ValueError("Unsupported thin Fusion Extrude or active wall controls")
    if Cursor.ReadWord() != 1:
        raise ValueError("Fusion distance Extrude requires one profile selection")
    ProxyId = ReadNativeRef(Cursor)
    ProfileId = ReadSelectDesc(BulkData, Owners, ProxyId, FeatureId)
    Profile = SelectCursor(BulkData, Owners, ProfileId, KProfileGuid)
    if DescOwner(Profile.DataValue) != FeatureId:
        raise ValueError("Fusion Extrude profile descriptor owner disagrees")
    SketchId, LoopId = ReadProfileRef(Profile.DataValue)
    SelectCursor(BulkData, Owners, SketchId, KExtrudeSketch)
    Loop = SelectCursor(BulkData, Owners, LoopId, KLoopGuid)
    if Loop.TakeBytes(2) != bytes(2) or ReadNativeRef(Loop) != ProfileId:
        raise ValueError("Fusion Extrude profile loop owner disagrees")
    return ProfileId, ProxyId
