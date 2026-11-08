# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.BodyInputs.BodyInput import BodyInputs
from convert.formats.Fusion.BodyInputs.InputRefs import ReadInputPicks
from convert.formats.Fusion.BodyInputs.ScaleControls import ReadScaleData
from convert.formats.Fusion.RecordSpan import RecordSpan


# the authored list follows a validated uniform or per axis factor layout
def ReadScaleInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Fields = ReadScaleData(BulkData, Owners, FeatureId)
    return BodyInputs(
        ReadInputPicks(BulkData, Owners, FeatureId, Fields.ProxyId, "input", 4)
    )
