from dataclasses import replace as Replace
from math import dist as Distance

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.Native import NativeDimension
from convert.adapters.solidworks.Core.RectBindings import (
    KPointToleranceMm,
    RectBindings,
)
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.ProfileSketch import ProfileSketch
from convert.adapters.solidworks.Sketch.GeometryTypes import KSketchDistance
from convert.adapters.solidworks.Sketch.MemberSpans import DistanceSpan
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import ConstraintRef, SketchRelation
from interchange.Records.RecordProvenance import ProvenanceSpan


# dimensions must share the exact authored perimeter endpoints in their archived operand order
def BoundDistRefs(
    RowValue: KSketchDistance, Binding: RectBindings
) -> tuple[ConstraintRef, ConstraintRef]:
    (FirstSlot, _), (SecondSlot, _) = RowValue["point_native_ids"]
    Members = {FirstSlot, SecondSlot}
    RequireArch(len(Members), 2, "distinct saved rectangle distance points")
    Edges = [
        EdgeValue for EdgeValue in Binding.Edges if set(EdgeValue.Slots) == Members
    ]
    RequireArch(len(Edges), 1, "distance belongs to one authored perimeter line")
    (Owner,) = Edges
    RequireArch(
        abs(
            Distance(Binding.Points[FirstSlot], Binding.Points[SecondSlot])
            - RowValue["metres"] * 1000
        )
        <= KPointToleranceMm,
        True,
        "distance scalar agrees with the saved point pair",
    )
    Start = ConstraintRef(Owner.Entity.id, "start")
    Finish = ConstraintRef(Owner.Entity.id, "end")
    return (Start, Finish) if Owner.Slots[0] == FirstSlot else (Finish, Start)


# the exact authored scalar must still be the existing public driving parameter
def CheckDistParam(
    Dimension: NativeDimension, RowValue: KSketchDistance, Source: DistanceSpan
) -> None:
    RequireArch(
        (RowValue["class"], Source.TypeCode, Source.ActivePair),
        ("sgPntPntDist", 1, True),
        "active unsigned two point distance",
    )
    RequireArch(
        Dimension.native_role in ("native", "driving"),
        True,
        "supported native parameter role",
    )
    RequireArch(
        (Dimension.kind, Dimension.native_offset, Dimension.native_value),
        ("length", Source.ScalarOffset, RowValue["metres"]),
        "typed scalar owns the existing public dimension",
    )
    RequireArch(
        Dimension.value_mm, RowValue["metres"] * 1000, "canonical millimetre value"
    )


# the distance body and scalar supply the saved kind and operands for the existing rule identity
def ApplyRectDist(
    RuleValue: SketchRelation,
    RowValue: KSketchDistance,
    Source: DistanceSpan,
    References: tuple[ConstraintRef, ConstraintRef],
    StreamName: str,
) -> SketchRelation:
    RequireArch(
        (RuleValue.driving, RuleValue.suppressed),
        (True, False),
        "active driving neutral rule",
    )
    Origin = RectSource(
        str(RowValue["native_id"]), StreamName, Source.Body, "sketch-distance"
    )
    Scalar = ProvenanceSpan(StreamName, Source.ScalarOffset, 8, "dimension-scalar")
    return Replace(
        RuleValue,
        kind="distance",
        references=References,
        provenance=Replace(Origin, spans=(*Origin.spans, Scalar)),
        attributes=FreezeMapping(
            {
                **RuleValue.attributes,
                "native_code": Source.TypeCode,
                "native_dimension_id": RowValue["native_id"],
                "native_point_ids": tuple(RowValue["point_native_ids"]),
                "native_point_handles": tuple(RowValue["point_handle_objects"]),
            }
        ),
    )


# complete rectangle dimensions must bind each saved value to one existing public relation
def BindRectDists(
    Rules: tuple[SketchRelation, ...],
    Profile: ProfileSketch,
    Binding: RectBindings,
    StreamName: str,
    Entries: tuple[tuple[NativeDimension, str], ...],
) -> tuple[SketchRelation, ...]:
    Dimensions = {ParamId: Dimension for Dimension, ParamId in Entries}
    Saved = {
        RowValue["name"]: (RowValue, Source)
        for RowValue, Source in zip(
            Profile.Geometry["length_dimensions"],
            Profile.Members.Distances,
            strict=True,
        )
    }
    RequireArch(
        (len(Saved), len(Profile.Members.Distances)),
        (2, 2),
        "two unique saved rectangle dimensions",
    )
    (First, _), (Second, _) = Saved.values()
    SharedPoints = set(First["point_native_ids"]) & set(Second["point_native_ids"])
    RequireArch(len(SharedPoints), 1, "two dimension edges share one perimeter corner")
    Result: list[SketchRelation] = []
    for RuleValue in Rules:
        if RuleValue.parameter_id is None:
            Result.append(RuleValue)
            continue
        Dimension = Dimensions[RuleValue.parameter_id]
        RowValue, Source = Saved.pop(Dimension.name)
        CheckDistParam(Dimension, RowValue, Source)
        References = BoundDistRefs(RowValue, Binding)
        Result.append(
            ApplyRectDist(RuleValue, RowValue, Source, References, StreamName)
        )
    RequireArch(
        len(Saved), 0, "every saved rectangle dimension owns a public constraint"
    )
    return tuple(Result)


# unsupported dimensions should leave the independently proven geometry and relations available
def ProjectDists(
    Rules: tuple[SketchRelation, ...],
    Profile: ProfileSketch,
    Binding: RectBindings,
    StreamName: str,
    Entries: tuple[tuple[NativeDimension, str], ...],
) -> tuple[SketchRelation, ...]:
    try:
        return BindRectDists(Rules, Profile, Binding, StreamName, Entries)
    except (KeyError, IndexError, ValueError):
        return Rules
