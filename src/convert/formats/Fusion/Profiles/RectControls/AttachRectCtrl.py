from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.Profiles.RectControls.CheckRectCorner import CheckRectCorner
from convert.formats.Fusion.Profiles.RectControls.ReadRectAxes import ReadRectAxes
from convert.formats.Fusion.Profiles.RectControls.ReadRectSizes import ReadRectSizes
from convert.formats.Fusion.Profiles.RectControls.RetainRectSize import RetainRectSize
from convert.formats.Fusion.Profiles.RectControls.SelectedSides import ReadRectSides
from convert.formats.Fusion.Profiles.RectControls.SketchDimRows import SketchDimRow
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch


# a rectangle keeps all original relations while adding only fully qualified contour associations
def AttachRectCtrl(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Feature: FeatureStep,
    DimRows: tuple[SketchDimRow, ...],
    GraphSpan: RecordSpan,
) -> Sketch:
    LoopId, Sides = ReadRectSides(BulkData, Owners, SketchValue, Feature)
    LoopSpan = Owners[LoopId]
    Geometric = SketchValue.constraints[:5]
    AxisRules = ReadRectAxes(Sides, Geometric)
    CornerId, Sizes = ReadRectSizes(Sides, DimRows, AxisRules)
    CheckRectCorner(SketchValue, Sides, Geometric, CornerId, len(DimRows) == 4)
    Updated = {
        Value.id: Value
        for Value in (
            RetainRectSize(RowValue, LoopSpan, GraphSpan) for RowValue in Sizes
        )
    }
    for Identity, AxisRule in AxisRules.items():
        Origin = AxisRule.provenance
        if Origin is None:
            raise ValueError("Fusion rectangle axis lacks native provenance")
        Updated[AxisRule.id] = Replace(
            AxisRule,
            provenance=Replace(
                Origin, spans=Origin.spans + ParamOrigin(LoopSpan).spans
            ),
            attributes=FreezeMapping(
                {
                    **AxisRule.attributes,
                    "fusion.selected_profile_side_id": Identity,
                    "fusion.selected_profile_loop_object_id": LoopId,
                }
            ),
        )
    return Replace(
        SketchValue,
        constraints=tuple(
            Updated.get(Value.id, Value) for Value in SketchValue.constraints
        ),
        attributes=FreezeMapping(
            {
                **SketchValue.attributes,
                "fusion.selected_profile_size_corner_object_id": CornerId,
            }
        ),
    )
