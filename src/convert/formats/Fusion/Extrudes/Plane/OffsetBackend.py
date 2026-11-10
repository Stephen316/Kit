# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import dist as Distance

from convert.formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.formats.Fusion.Extrudes.Plane.OffsetOrigin import ReadOffsetOrg
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.ParamProjection import ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadDescLeaf, ReadEntityLeaf
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# the owned backend distinguishes offset from other methods sharing the cached frame mode
KOffsetBackend = "7B6C3C2D-4096-4E6D-B225-699E8C2D9355"


# spatial comparison preserves independent cached and regenerated plane frame evidence
def VectorCoords(Value: SpaceVector) -> tuple[float, float, float]:
    return Value.x, Value.y, Value.z


# the explicit origin support and scalar must regenerate the selected cached frame
def CheckOffsetDef(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    PlaneId: int,
    FeatureId: int,
    ComponentId: int,
    FrameValue: Transform,
) -> tuple[int, ...]:
    Feature = SelectCursor(BulkData, Owners, FeatureId, KPlaneFeature)
    if Feature.TakeBytes(3) != b"\0\0\1" or Feature.ReadWord() != 0:
        raise ValueError("Unsupported Fusion Offset plane feature variant")
    ExtraId = ReadNativeRef(Feature)
    if Feature.TakeBytes(1) != b"\1" or ReadNativeRef(Feature) != PlaneId:
        raise ValueError("Fusion Offset plane feature geometry disagrees")
    BackendId = ReadNativeRef(Feature)
    ScalarId, SupportId = ReadOffsetWire(
        BulkData, Owners, BackendId, ExtraId, FeatureId
    )
    Extra = CheckExtBinding(BulkData, Owners, FeatureId, ExtraId, "ExtraOffset")
    Scalar = CheckExtBinding(BulkData, Owners, FeatureId, ScalarId, "AlongDistance")
    if (
        ParamQuantity(Extra).unit != "cm"
        or Extra.Number != 0.0
        or ParamQuantity(Scalar).unit != "cm"
    ):
        raise ValueError("Unsupported Fusion Offset plane scalar units or extra offset")
    LeafId = ReadDescLeaf(BulkData, Owners, SupportId, FeatureId)
    OriginId = ReadEntityLeaf(BulkData, Owners, LeafId)
    OriginFrame, ContainerId = ReadOffsetOrg(BulkData, Owners, OriginId, ComponentId)
    Expected = OffsetVector(
        OriginFrame.origin, OriginFrame.z_axis, Scalar.Number * 10.0
    )
    if not Distance(
        VectorCoords(Expected), VectorCoords(FrameValue.origin)
    ) <= 1e-9 or any(
        Distance(VectorCoords(Cached), VectorCoords(Origin)) > 1e-10
        for Cached, Origin in (
            (FrameValue.x_axis, OriginFrame.x_axis),
            (FrameValue.y_axis, OriginFrame.y_axis),
            (FrameValue.z_axis, OriginFrame.z_axis),
        )
    ):
        raise ValueError(
            "Fusion Offset plane scalar and origin frame disagree with cache"
        )
    return BackendId, ExtraId, ScalarId, SupportId, LeafId, OriginId, ContainerId


# the offset backend must identify the same owner and expose exactly one origin support
def ReadOffsetWire(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    BackendId: int,
    ExtraId: int,
    FeatureId: int,
) -> tuple[int, int]:
    Backend = SelectCursor(BulkData, Owners, BackendId, KOffsetBackend)
    if (
        Backend.TakeBytes(36) != bytes(36)
        or Backend.TakeBytes(2) != b"\1\0"
        or ReadNativeRef(Backend) != ExtraId
    ):
        raise ValueError("Unsupported Fusion Offset plane backend framing")
    _ = Backend.TakeBytes(171)
    if (
        Backend.ReadWord() != 2
        or Backend.TakeBytes(1) != bytes(1)
        or Backend.ReadWord() != 1
    ):
        raise ValueError("Unsupported Fusion selected plane definition method")
    ScalarId = ReadNativeRef(Backend)
    if Backend.ReadWord() != 1:
        raise ValueError("Fusion Offset plane requires one origin support")
    SupportId = ReadNativeRef(Backend)
    if len(Backend.DataValue) - Backend.Offset != 88:
        raise ValueError("Unsupported Fusion Offset plane backend extent")
    Backend.Offset = len(Backend.DataValue) - 11
    if ReadNativeRef(Backend) != FeatureId:
        raise ValueError("Fusion Offset plane backend owner disagrees")
    return ScalarId, SupportId
