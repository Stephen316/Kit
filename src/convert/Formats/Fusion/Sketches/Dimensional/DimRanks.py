from collections import Counter

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.Dimensional.DimRecord import (
    DimRecordBody,
    NativeDimension,
    ReadDimRecord,
)
from convert.Formats.Fusion.Sketches.Dimensional.DimScope import DimensionScope
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import KDimensionSpecs
from convert.Formats.Fusion.Sketches.Geometric.GeomRuleKinds import GetGeomRuleKind
from convert.Formats.Fusion.Sketches.Geometric.GeomRuleRecord import (
    KGeomRuleGuid,
    ReadGeomRule,
)


# a recorded slot can witness order only when all preceding uses have known sketch ownership
def ClaimRanksMut(
    Counts: Counter[int],
    Scope: DimensionScope,
    Identities: tuple[int, ...],
    Slots: tuple[int, ...],
) -> tuple[int, ...]:
    Ranks = tuple(Counts[Identity] for Identity in Identities)
    if Ranks != Slots or any(Identity not in Scope.Entities for Identity in Identities):
        raise ValueError("Unresolved Fusion sketch operand rank")
    Counts.update(Identities)
    return Ranks


# the complete native member lists establish the scope of nonzero dimension slots
def ReadDimRanks(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    RootSpan: RecordSpan,
    Scope: DimensionScope,
    Geometric: tuple[int, ...],
    Dimensions: tuple[int, ...],
) -> dict[int, tuple[int, ...]]:
    Counts: Counter[int] = Counter()
    for Identity in Geometric:
        Record = Owners.get(Identity)
        if Record is None or Record.ClassGuid != KGeomRuleGuid:
            raise ValueError("Unresolved Fusion rank witness relation")
        RuleValue = ReadGeomRule(DimRecordBody(BulkData, Record))
        if RuleValue.OwnerId != RootSpan.ObjectId:
            raise ValueError("Fusion rank witness relation belongs to another sketch")
        _ = ClaimRanksMut(
            Counts, Scope, RuleValue.Dependencies, (0,) * len(RuleValue.Dependencies)
        )
        _ = GetGeomRuleKind(
            RuleValue.CodeValue,
            tuple(Scope.Entities[Operand].kind for Operand in RuleValue.Arguments),
        )
    Result: dict[int, tuple[int, ...]] = {}
    for Identity in Dimensions:
        Record = Owners.get(Identity)
        if Record is None:
            raise ValueError("Unresolved Fusion rank witness dimension")
        Native = ReadDimRecord(DimRecordBody(BulkData, Record), Record.ClassGuid)
        SpecValue = KDimensionSpecs.get(Native.Code)
        if SpecValue is None or SpecValue.ClassGuid != Record.ClassGuid:
            raise ValueError("Unqualified Fusion rank witness dimension")
        Result[Identity] = ClaimRanksMut(
            Counts, Scope, Native.DependencyIds, Native.DependencySlots
        )
        if (
            tuple(Scope.Entities[Operand].kind for Operand in Native.TargetIds)
            != SpecValue.Targets
        ):
            raise ValueError("Unqualified Fusion rank witness operands")
    return Result


# relations need the original dependencies when their layout requires independent rank evidence
def DimRankAttrs(
    Native: NativeDimension, MemberRanks: tuple[int, ...] | None
) -> dict[str, object]:
    if Native.TargetIds == Native.DependencyIds and not any(Native.DependencySlots):
        return {}
    if Native.DependencySlots != MemberRanks:
        raise ValueError(
            "Fusion dimension operand slots disagree with sketch membership"
        )
    return {
        "fusion.dimension_dependency_object_ids": Native.DependencyIds,
        "fusion.dimension_dependency_slots": Native.DependencySlots,
    }
