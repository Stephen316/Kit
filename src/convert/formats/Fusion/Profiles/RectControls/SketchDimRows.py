from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Sketches.SketchRuleIds import ReadSketchRules
from convert.formats.Fusion.Sketches.SketchRuleScope import ReadSketchRoot
from interchange.geometry.models.Sketch import Sketch, SketchRelation
from interchange.records.RecordParameter import Parameter


# graph checks need both the neutral row and the actual saved dependency operands
@MakeDataClass(frozen=True, slots=True)
class SketchDimRow:
    Relation: SketchRelation
    RelationId: int
    BindId: int
    ValueId: int
    OwnerId: int


# both stored native lists must exhaust the already projected relation roster
def ReadSketchDims(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Params: dict[str, Parameter],
    ExpectedDims: int,
) -> tuple[SketchDimRow, ...]:
    RootSpan = ReadSketchRoot(SketchValue, Owners)
    Geometric, Dimensions = ReadSketchRules(BulkData, RootSpan)
    Relations = SketchValue.constraints
    Actual = tuple(
        int(Value.provenance.native_id)
        for Value in Relations
        if Value.provenance is not None
    )
    if (
        len(Geometric) != 5
        or len(Dimensions) != ExpectedDims
        or len(Actual) != len(Relations)
        or Actual != Geometric + Dimensions
    ):
        raise ValueError(
            "Fusion rectangle lacks its complete native relation inventory"
        )
    Cursor = MetaCursor(BulkData[RootSpan.EndOffset - 15 : RootSpan.EndOffset - 4])
    OwnerId = ReadNativeRef(Cursor)
    _ = SelectCursor(BulkData, Owners, OwnerId, KSketchFeature)
    DimRows: list[SketchDimRow] = []
    for Relation, RelationId in zip(Relations[5:], Dimensions, strict=True):
        Value = Params.get(Relation.parameter_id or "")
        BindId = Relation.attributes.get("fusion.binding_id")
        if (
            Value is None
            or Value.provenance is None
            or type(BindId) is not int
            or Value.attributes.get("fusion.binding_id") != BindId
            or Value.attributes.get("fusion.owner_object_id") != OwnerId
        ):
            raise ValueError(
                "Fusion rectangle dimension binding and sketch owner disagree"
            )
        DimRows.append(
            SketchDimRow(
                Relation, RelationId, BindId, int(Value.provenance.native_id), OwnerId
            )
        )
    return tuple(DimRows)
