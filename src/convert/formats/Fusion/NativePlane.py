# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace

from convert.formats.Fusion.FeatureLabels import ReadLabelData
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.PlaneAxes import ReadPlaneAxes
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.SupportPlane import SupportPlane

# registry class identity limits projection to known construction plane features
KPlaneFeature = "D869265F-F339-4751-A066-91D30F81FF08"

# the feature must point to a registered plane geometry object
KPlaneObject = "8D424E29-DE23-4B1F-A3AD-84C52A497D1A"


# reciprocal references and the shared ordinal qualify the native plane frame
def ReadNativePlane(
    BulkData: bytes, Feature: RecordSpan, Owners: dict[int, RecordSpan]
) -> SupportPlane:
    BodyValue = BulkData[Feature.PayloadOffset + 4 : Feature.EndOffset]
    LabelData = ReadLabelData(BodyValue, "WorkPlane")
    if LabelData is None:
        raise ValueError("Missing Fusion construction plane feature ordinal")
    RefCursor = MetaCursor(BodyValue)
    RefCursor.Offset = 19
    PlaneId = ReadNativeRef(RefCursor)
    PlaneSpan = Owners.get(PlaneId)
    if PlaneSpan is None or PlaneSpan.ClassGuid != KPlaneObject:
        raise ValueError("Missing typed Fusion construction plane geometry")
    Cursor = MetaCursor(BulkData[PlaneSpan.PayloadOffset + 4 : PlaneSpan.EndOffset])
    if (
        Cursor.TakeBytes(2) != b"\0\1"
        or Cursor.ReadWord() != 1
        or Cursor.ReadText() != "EntityGenesis"
        or Cursor.ReadText() != "IntrinsicMetaTypeuint64"
        or Cursor.ReadLong() != 0
    ):
        raise ValueError("Unsupported Fusion construction plane attributes")
    ModeValue = Cursor.ReadWord()
    _ = Cursor.TakeBytes(16)
    if ModeValue not in (1, 2) or Cursor.TakeBytes(1) != b"\0":
        raise ValueError("Unsupported Fusion construction plane frame")
    Transform = ReadPlaneAxes(Cursor.TakeBytes(72))
    _ = Cursor.TakeBytes(16)
    _ = Cursor.ReadText(True, Maximum=1024)
    CollectionId = ReadNativeRef(Cursor)
    if (
        Cursor.ReadLong() != LabelData[1]
        or Cursor.TakeBytes(1) != b"\0"
        or ReadNativeRef(Cursor) != Feature.ObjectId
        or Cursor.TakeBytes(2) != b"\0\1"
    ):
        raise ValueError("Fusion construction plane owner or ordinal disagrees")
    NameValue = Cursor.ReadText(True, Maximum=1024)
    Origin = RecordOrigin(PlaneSpan)
    return SupportPlane(
        id=f"fusion-plane-{PlaneId}",
        name=NameValue,
        transform=Transform,
        provenance=Replace(Origin, spans=Origin.spans + RecordOrigin(Feature).spans),
        attributes=FreezeMapping(
            {
                "fusion.feature_object_id": Feature.ObjectId,
                "fusion.cached_plane_mode": ModeValue,
                "fusion.plane_collection_id": CollectionId,
                "fusion.coordinate_space": "component",
            }
        ),
    )
