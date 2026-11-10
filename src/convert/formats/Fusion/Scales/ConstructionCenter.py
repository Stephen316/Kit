# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import dist as Distance

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.Scales.OriginCenter import KWorkPoint
from convert.formats.Fusion.Scales.PointBackend import ReadPointBack, ReadSpatialPt
from convert.formats.Fusion.Scales.PointCollection import CheckPointList
from convert.formats.Fusion.Scales.SketchCenter import ReadSketchPt
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.SelectionRef import ReadDescLeaf
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.VectorSpace import SpaceVector

# the work point feature proves its own authored construction method
KWorkPointStep = "5F40832C-61AA-4A05-95B1-EFA0BA483138"


# independent coordinate copies corroborate a selected point without choosing identity
def CheckCenterPt(First: SpaceVector, Second: SpaceVector) -> None:
    if Distance((First.x, First.y, First.z), (Second.x, Second.y, Second.z)) > 1e-8:
        raise ValueError("Fusion selected point coordinates disagree")


# a by point feature retains its named support rather than trusting its stored coordinates
def ReadWorkPoint(
    BulkData: bytes,
    Context: InputContext,
    Document: CadDocument,
    Receiver: FeatureStep,
    Scope: CreatorScope,
    PointId: int,
) -> tuple[SpaceVector, str, str, str]:
    Owners = Context.Owners
    Cursor = SelectCursor(BulkData, Owners, PointId, KWorkPoint)
    if ReadGeomAttrs(Cursor) != {"EntityGenesis": 0}:
        raise ValueError("Unsupported Fusion construction point attributes")
    Cached = ReadSpatialPt(Cursor)
    if not Cursor.ReadText(True, Maximum=128).startswith("0_"):
        raise ValueError("Unsupported Fusion construction point label")
    CollectionId = ReadNativeRef(Cursor)
    _ = Cursor.ReadLong()
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion construction point owner framing")
    FeatureId = ReadNativeRef(Cursor)
    Cursor.Offset = len(Cursor.DataValue) - 11
    if ReadNativeRef(Cursor) != CollectionId:
        raise ValueError("Fusion construction point collection backlink disagrees")
    CheckPointList(BulkData, Owners, CollectionId, PointId, Scope.ComponentId)
    Source = Context.Steps.get(FeatureId)
    if (
        Source is None
        or Source.order >= Receiver.order
        or not IsSavedActive(Source)
        or Context.Scopes.get(FeatureId) != Scope
    ):
        raise ValueError(
            "Fusion construction point lacks a preceding same scope feature"
        )
    Derived, SketchId, EntityId = ReadPointLeaf(
        BulkData, Context, Document, Source, Scope, PointId, FeatureId
    )
    CheckCenterPt(Derived, Cached)
    return Derived, Source.id, SketchId, EntityId


# the authored point feature must prove its sketch entity before cached coordinates can be trusted
def ReadPointLeaf(
    BulkData: bytes,
    Context: InputContext,
    Document: CadDocument,
    Source: FeatureStep,
    Scope: CreatorScope,
    PointId: int,
    FeatureId: int,
) -> tuple[SpaceVector, str, str]:
    Owners = Context.Owners
    Feature = SelectCursor(BulkData, Owners, FeatureId, KWorkPointStep)
    if (
        Feature.TakeBytes(11) != b"\x00\x00\x01" + bytes(8)
        or ReadNativeRef(Feature) != PointId
    ):
        raise ValueError("Fusion construction point feature is not an owned ByPoint")
    Point, Method, Descriptor = ReadPointBack(
        BulkData, Owners, ReadNativeRef(Feature), FeatureId
    )
    if Method != 10:
        raise ValueError("Unsupported Fusion ByPoint support method")
    LeafId = ReadDescLeaf(BulkData, Owners, Descriptor, FeatureId)
    Derived, SketchValue, Entity = ReadSketchPt(
        BulkData, Context, Document, Source, Scope, LeafId
    )
    CheckCenterPt(Derived, Point)
    return Derived, SketchValue.id, Entity.id
