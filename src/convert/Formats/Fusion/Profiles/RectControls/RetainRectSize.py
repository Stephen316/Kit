from dataclasses import replace as Replace

from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.Profiles.RectControls.ReadRectSizes import ChosenSize
from convert.Formats.Fusion.Profiles.RectControls.RectSideOrigin import RectSideOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import SketchRelation


# size provenance appends the exact side and reciprocal owner edge beside the original ordered point operands
def RetainRectSize(
    Chosen: ChosenSize,
    Scope: RectSideOrigin,
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
                f"{Scope.Prefix}_side_id": SideValue.id,
                Scope.IdentityKey: Scope.Record.ObjectId,
                f"{Scope.Prefix}_axis_relation_id": Chosen.AxisRule.id,
                f"{Scope.Prefix}_binding_edge": (
                    RowValue.OwnerId,
                    RowValue.BindId,
                    1,
                ),
            }
        ),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + ParamOrigin(Scope.Record).spans
            + SideValue.provenance.spans
            + Chosen.AxisRule.provenance.spans
            + ParamOrigin(GraphSpan).spans,
        ),
    )
