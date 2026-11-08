# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Extrudes.ExtrudeBinding import (
    CheckExtBinding,
    KExtrudeCache,
)
from convert.formats.Fusion.Extrudes.Plane.PlaneExtFields import PlaneExtFields
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.ParamProjection import ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor


# only verified owned untapered distance and offset values qualify as plane extents
def CheckPlaneNums(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    Fields: PlaneExtFields,
) -> None:
    Cache = SelectCursor(BulkData, Owners, Fields.CacheId, KExtrudeCache)
    if (
        len(Cache.DataValue) != 81
        or Cache.TakeBytes(2) != bytes(2)
        or ReadNativeRef(Cache) != FeatureId
    ):
        raise ValueError("Unsupported Fusion selected plane Extrude cache")
    Cache.Offset = 70
    if ReadNativeRef(Cache) != FeatureId:
        raise ValueError("Fusion selected plane Extrude cache owner disagrees")
    Offset = CheckExtBinding(
        BulkData,
        Owners,
        FeatureId,
        Fields.OffsetId,
        "ProfileOffset" if Fields.Role == "start" else "Side1Offset",
    )
    Taper = CheckExtBinding(BulkData, Owners, FeatureId, Fields.TaperId, "TaperAngle")
    if (
        ParamQuantity(Offset).unit != "cm"
        or Offset.Number < 0.0
        or ParamQuantity(Taper).unit != "rad"
        or Taper.Number != 0.0
    ):
        raise ValueError("Unsupported Fusion selected plane Extrude offset or taper")
    if Fields.AlongId is not None:
        Along = CheckExtBinding(
            BulkData, Owners, FeatureId, Fields.AlongId, "AlongDistance"
        )
        if ParamQuantity(Along).unit != "cm" or Along.Number <= 0.0:
            raise ValueError("Fusion selected start plane requires positive distance")
