from dataclasses import replace as Replace

from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.Profiles.RectControls.CheckRectCorner import CheckRectCorner
from convert.Formats.Fusion.Profiles.RectControls.ReadAuthored import ReadAuthored
from convert.Formats.Fusion.Profiles.RectControls.ReadRectAxes import ReadRectAxes
from convert.Formats.Fusion.Profiles.RectControls.ReadRectSizes import ReadRectSizes
from convert.Formats.Fusion.Profiles.RectControls.RectSideOrigin import RectSideOrigin
from convert.Formats.Fusion.Profiles.RectControls.RetainRectSize import RetainRectSize
from convert.Formats.Fusion.Profiles.RectControls.SelectedSides import ReadRectSides
from convert.Formats.Fusion.Profiles.RectControls.SketchDimRows import SketchDimRow
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch


# a rectangle keeps all original relations while adding only fully qualified contour associations
def AttachRectCtrl(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Feature: FeatureStep | None,
    DimRows: tuple[SketchDimRow, ...],
    GraphSpan: RecordSpan,
) -> Sketch:
    if Feature is None:
        Source, Sides = ReadAuthored(BulkData, Owners, SketchValue)
    else:
        LoopId, Sides = ReadRectSides(BulkData, Owners, SketchValue, Feature)
        Source = Owners[LoopId]
    Scope = RectSideOrigin(Source)
    Geometric = SketchValue.constraints[:5]
    AxisRules = ReadRectAxes(Sides, Geometric)
    CornerId, Sizes = ReadRectSizes(Sides, DimRows, AxisRules)
    CheckRectCorner(SketchValue, Sides, Geometric, CornerId, len(DimRows) == 4)
    Updated = {
        Value.id: Value
        for Value in (RetainRectSize(RowValue, Scope, GraphSpan) for RowValue in Sizes)
    }
    for Identity, AxisRule in AxisRules.items():
        Origin = AxisRule.provenance
        if Origin is None:
            raise ValueError("Fusion rectangle axis lacks native provenance")
        Updated[AxisRule.id] = Replace(
            AxisRule,
            provenance=Replace(Origin, spans=Origin.spans + ParamOrigin(Source).spans),
            attributes=FreezeMapping(
                {
                    **AxisRule.attributes,
                    f"{Scope.Prefix}_side_id": Identity,
                    Scope.IdentityKey: Source.ObjectId,
                }
            ),
        )
    Attributes = {
        **SketchValue.attributes,
        f"{Scope.Prefix}_size_corner_object_id": CornerId,
    }
    if Feature is None:
        Attributes["fusion.authored_contour_entity_ids"] = tuple(
            Value.Entity.id for Value in Sides
        )
    return Replace(
        SketchValue,
        constraints=tuple(
            Updated.get(Value.id, Value) for Value in SketchValue.constraints
        ),
        attributes=FreezeMapping(Attributes),
    )
