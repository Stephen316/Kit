from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.Profiles.RectControls.ReadRectSizes import ChosenSize
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Sketch import SketchRelation


# size provenance appends the exact side and reciprocal owner edge beside the original ordered point operands
def RetainRectSize(
    Chosen: ChosenSize,
    LoopSpan: RecordSpan,
    GraphSpan: RecordSpan,
) -> SketchRelation:
    RowValue = Chosen.SizeRow
    Relation = RowValue.Relation
    SideValue = Chosen.SideValue.Entity
    if (
        Relation.provenance is None
        or SideValue.provenance is None
        or Chosen.AxisRule.provenance is None
    ):
        raise ValueError("Fusion rectangle size lacks native side provenance")
    Origin = Relation.provenance
    return Replace(
        Relation,
        attributes=FreezeMapping(
            {
                **Relation.attributes,
                "fusion.selected_profile_side_id": SideValue.id,
                "fusion.selected_profile_loop_object_id": LoopSpan.ObjectId,
                "fusion.selected_profile_axis_relation_id": Chosen.AxisRule.id,
                "fusion.selected_profile_binding_edge": (
                    RowValue.OwnerId,
                    RowValue.BindId,
                    1,
                ),
            }
        ),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + ParamOrigin(LoopSpan).spans
            + SideValue.provenance.spans
            + Chosen.AxisRule.provenance.spans
            + ParamOrigin(GraphSpan).spans,
        ),
    )
