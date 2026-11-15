from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Profiles.RectControls.SelectedSides import SelectedSide
from convert.formats.Fusion.Profiles.RectControls.SketchDimRows import SketchDimRow
from interchange.enums.EnumGeometry import ConstraintKind
from interchange.geometry.models.Sketch import SketchRelation

# a signed component size must use the saved axis of the same owned line
KSizeAxes = {
    ConstraintKind.KDistanceX.value: ConstraintKind.KHorizontal.value,
    ConstraintKind.KDistanceY.value: ConstraintKind.KVertical.value,
}


# a size relation retains the side and the independent geometric axis witness
@MakeDataClass(frozen=True, slots=True)
class ChosenSize:
    SizeRow: SketchDimRow
    SideValue: SelectedSide
    AxisRule: SketchRelation


# literal dimension point order selects a side before any length comparison
def ReadRectSizes(
    Sides: tuple[SelectedSide, ...],
    DimRows: tuple[SketchDimRow, ...],
    AxisRules: dict[str, SketchRelation],
) -> tuple[int, tuple[ChosenSize, ...]]:
    ByEnds = {
        tuple(
            f"fusion-sketch-entity-{Identity}"
            for Identity in (Value.StartId, Value.FinishId)
        ): Value
        for Value in Sides
    }
    Sizes: list[ChosenSize] = []
    for RowValue in DimRows:
        Relation = RowValue.Relation
        RefsValue = tuple(Value.entity_id for Value in Relation.references)
        SideValue = ByEnds.get(RefsValue)
        if SideValue is None:
            continue
        AxisRule = AxisRules[SideValue.Entity.id]
        if not Relation.driving or KSizeAxes.get(Relation.kind) != AxisRule.kind:
            raise ValueError("Fusion selected dimension and native side axes disagree")
        Sizes.append(ChosenSize(RowValue, SideValue, AxisRule))
    if len(Sizes) != 2 or {Value.SizeRow.Relation.kind for Value in Sizes} != set(
        KSizeAxes
    ):
        raise ValueError("Fusion selected rectangle lacks two native size sides")
    First, Second = (Value.SideValue for Value in Sizes)
    Shared = {First.StartId, First.FinishId} & {Second.StartId, Second.FinishId}
    if len(Shared) != 1:
        raise ValueError("Fusion selected size sides do not share one native corner")
    return next(iter(Shared)), tuple(Sizes)
