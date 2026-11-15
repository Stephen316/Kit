from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.cut.CutLoop import (
    CutLineEntity,
    OrderCutLines,
    ReadCutLines,
)
from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from interchange.geometry.models.Sketch import ConstraintRef, Sketch


# each rule target must retain the same source point slots as the published perimeter
@Dataclass(frozen=True, slots=True)
class CutRuleLine:
    EntityId: str
    Slots: tuple[int, int]


# the already placed perimeter must still be the exact configuration lines
def MatchRuleLines(
    SketchValue: Sketch, Source: CutRuleSource
) -> dict[int, CutRuleLine]:
    Lines = OrderCutLines(ReadCutLines(Source.SketchData))
    Points = Source.SketchData.Geometry["points_metres"]
    Entities = {Value.id: Value for Value in SketchValue.entities}
    Expected = tuple(
        CutLineEntity(Value, Points, SketchValue.id, Source.ConfigStream)
        for Value in Lines
    )
    RequireArch(
        SketchValue.closed_profile_entity_ids,
        (tuple(Value.id for Value in Expected),),
        "saved cut lines still own the current loop",
    )
    Result: dict[int, CutRuleLine] = {}
    for LineValue, Entity in zip(Lines, Expected, strict=True):
        RequireArch(
            Entities[Entity.id],
            Entity,
            "current cut line agrees with saved configuration",
        )
        Result[LineValue.Source["native_id"]] = CutRuleLine(Entity.id, LineValue.Slots)
    return Result


# a native edge distance preserves its operand order through the directed neutral loop
def MatchDistEdge(
    Lines: dict[int, CutRuleLine], Slots: tuple[int, int]
) -> tuple[ConstraintRef, ConstraintRef]:
    Members = set(Slots)
    Matches = [Value for Value in Lines.values() if set(Value.Slots) == Members]
    RequireArch(len(Matches), 1, "cut size belongs to one actual perimeter line")
    (LineValue,) = Matches
    First = ConstraintRef(LineValue.EntityId, "start")
    Second = ConstraintRef(LineValue.EntityId, "end")
    return (First, Second) if LineValue.Slots == Slots else (Second, First)


# a cut corner uses the unique outgoing endpoint of the already closed perimeter
def MatchCutCorner(Lines: dict[int, CutRuleLine], SlotValue: int) -> ConstraintRef:
    Matches = [Value for Value in Lines.values() if Value.Slots[0] == SlotValue]
    RequireArch(len(Matches), 1, "unique projected cut corner")
    return ConstraintRef(Matches[0].EntityId, "start")
