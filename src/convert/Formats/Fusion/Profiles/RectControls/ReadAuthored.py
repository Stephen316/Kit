from convert.Formats.Fusion.Profiles.RectControls.SelectedSides import (
    ReadRectEnds,
    SelectedSide,
)
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.SketchRuleScope import ReadSketchRoot
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.Models.Sketch import Sketch


# a sketch only rectangle gets its contour from the complete authored primitive roster
def ReadAuthored(
    BulkData: bytes, Owners: dict[int, RecordSpan], SketchValue: Sketch
) -> tuple[RecordSpan, tuple[SelectedSide, ...]]:
    RootSpan = ReadSketchRoot(SketchValue, Owners)
    if RootSpan.EndOffset - RootSpan.PayloadOffset - 4 != 199:
        raise ValueError("Unsupported Fusion standalone rectangle sketch framing")
    Members = tuple(
        Value
        for Value in SketchValue.entities
        if isinstance(Value.geometry, LineGeometry)
    )
    if (
        SketchValue.closed_profile_entity_ids
        or len(Members) != 4
        or sum(
            isinstance(Value.geometry, PointGeometry) for Value in SketchValue.entities
        )
        != 5
        or len(SketchValue.entities) != 9
    ):
        raise ValueError(
            "Fusion standalone rectangle lacks its complete authored primitive roster"
        )
    return RootSpan, ReadRectEnds(
        BulkData, Owners, SketchValue, RootSpan.ObjectId, Members
    )
