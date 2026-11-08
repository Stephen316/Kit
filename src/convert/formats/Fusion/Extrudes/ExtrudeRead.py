# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Extrudes.ExtrudeBinding import CheckExtInputs
from convert.formats.Fusion.Extrudes.ExtrudeControl import ReadExtControls
from convert.formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.formats.Fusion.Extrudes.NativeExtrude import NativeExtrude
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# a typed feature boundary limits every distance control read
KExtrudeGuid = "DD405BC2-D673-44F0-8833-5CB2A1C186C7"


# only qualified solid distance controls and an owned profile form a native extrude definition
def ReadExtrude(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> NativeExtrude:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    Fields = ReadExtControls(Cursor)
    ProfileId, ProxyId = ReadExtProfile(
        BulkData, Owners, Cursor, FeatureId, Fields.SideMode
    )
    CheckExtInputs(BulkData, Owners, FeatureId, Fields)
    return NativeExtrude(
        Fields.AlongId,
        Fields.AgainstId,
        Fields.StartId,
        Fields.TaperId,
        Fields.SecondTaperId,
        Fields.SideMode,
        Fields.Direction,
        ProfileId,
        ProxyId,
    )
