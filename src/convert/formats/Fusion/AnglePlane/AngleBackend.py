# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.Extrudes.Plane.OffsetBackend import KOffsetBackend
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor


# the owned method and its support order distinguish angle from other plane variants
def ReadAngleBack(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int, PlaneId: int
) -> tuple[int, int, int, int, int]:
    Feature = SelectCursor(BulkData, Owners, FeatureId, KPlaneFeature)
    if Feature.TakeBytes(3) != b"\0\0\1" or Feature.ReadWord() != 5:
        raise ValueError("Unsupported Fusion Angle plane feature variant")
    ExtraId = ReadNativeRef(Feature)
    if Feature.TakeBytes(1) != b"\1" or ReadNativeRef(Feature) != PlaneId:
        raise ValueError("Fusion Angle plane feature geometry disagrees")
    BackendId = ReadNativeRef(Feature)
    Backend = SelectCursor(BulkData, Owners, BackendId, KOffsetBackend)
    Prefix = {347: 29, 354: 36}.get(len(Backend.DataValue))
    if (
        Prefix is None
        or Backend.TakeBytes(Prefix) != bytes(Prefix)
        or Backend.TakeBytes(2) != b"\1\0"
        or ReadNativeRef(Backend) != ExtraId
    ):
        raise ValueError("Unsupported Fusion Angle plane backend framing")
    _ = Backend.TakeBytes(171)
    if (
        Backend.ReadWord() != 3
        or Backend.TakeBytes(1) != b"\0"
        or Backend.ReadWord() != 1
    ):
        raise ValueError("Unsupported Fusion Angle plane method or scalar count")
    AngleId = ReadNativeRef(Backend)
    if Backend.ReadWord() != 2:
        raise ValueError("Fusion Angle plane requires an axis and a datum")
    AxisDesc, BaseDesc = ReadNativeRef(Backend), ReadNativeRef(Backend)
    if len(Backend.DataValue) - Backend.Offset != 88:
        raise ValueError("Unsupported Fusion Angle plane backend extent")
    Backend.Offset = len(Backend.DataValue) - 11
    if ReadNativeRef(Backend) != FeatureId:
        raise ValueError("Fusion Angle plane backend owner disagrees")
    return BackendId, ExtraId, AngleId, AxisDesc, BaseDesc
