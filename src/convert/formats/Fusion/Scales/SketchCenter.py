# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.VectorSpace import SpaceVector

# a point selector identifies an authored sketch vertex through its stored entity tag
KSketchPtLeaf = "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF"


# named point resolution uses native tag and sketch scope before comparing coordinates
def ReadSketchPt(
    BulkData: bytes,
    Context: InputContext,
    Document: CadDocument,
    Receiver: FeatureStep,
    Scope: CreatorScope,
    LeafId: int,
) -> tuple[SpaceVector, Sketch, SketchEntity]:
    Cursor = SelectCursor(BulkData, Context.Owners, LeafId, KSketchPtLeaf)
    if len(Cursor.DataValue) != 18 or Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion sketch point selector")
    SketchId, TagValue = Cursor.ReadLong(), Cursor.ReadLong()
    Sketches = tuple(
        Value
        for Value in Document.sketches
        if Value.provenance is not None and Value.provenance.native_id == str(SketchId)
    )
    if len(Sketches) != 1:
        raise ValueError("Fusion selected point sketch is missing or ambiguous")
    (SketchValue,) = Sketches
    Steps = tuple(
        Value
        for Identity, Value in Context.Steps.items()
        if Value.sketch_id == SketchValue.id and Context.Scopes.get(Identity) == Scope
    )
    Frames = tuple(
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
        and Value.attributes.get("fusion.component_object_id") == Scope.ComponentId
    )
    if (
        len(Steps) != 1
        or Steps[0].order >= Receiver.order
        or not IsSavedActive(Steps[0])
        or len(Frames) != 1
    ):
        raise ValueError("Fusion selected point lacks a preceding same scope sketch")
    Matches = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, PointGeometry)
        and Value.attributes.get("fusion.entity_tag") == TagValue
    )
    if len(Matches) != 1 or not isinstance(Matches[0].geometry, PointGeometry):
        raise ValueError("Fusion selected sketch point tag is missing or ambiguous")
    (Entity,) = Matches
    Geometry = Matches[0].geometry
    return (
        PlacePrismPoint(Frames[0].transform, Geometry.point, 0.0),
        SketchValue,
        Entity,
    )
