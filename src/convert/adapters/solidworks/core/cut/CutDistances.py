from dataclasses import replace as Replace
from math import hypot as Hypot

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectBindings import KPointToleranceMm
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.core.cut.CutDimRoles import CutDimRole
from convert.adapters.solidworks.core.cut.CutOrigin import CutOriginPoint
from convert.adapters.solidworks.core.cut.CutRuleLines import (
    CutRuleLine,
    MatchCutCorner,
    MatchDistEdge,
)
from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Sketch import ConstraintRef, SketchRelation
from interchange.records.RecordProvenance import ProvenanceSpan


# both cut offsets must relate the same owned proxy and perimeter corner
def CutOffsetRefs(
    RoleValue: CutDimRole, Origin: CutOriginPoint, Lines: dict[int, CutRuleLine]
) -> tuple[ConstraintRef, ...]:
    Points = RoleValue.RowValue["point_native_ids"]
    RequireArch(Points.count(Origin.PointId), 1, "offset has one owned origin proxy")
    return tuple(
        (
            ConstraintRef(Origin.Entity.id)
            if PointId == Origin.PointId
            else MatchCutCorner(Lines, PointId[0])
        )
        for PointId in Points
    )


# the cached scalar must agree with the actual signed local coordinate difference
def MeasureCutRule(RoleValue: CutDimRole, Source: CutRuleSource) -> float:
    Points = Source.SketchData.Geometry["points_metres"]
    (First, _), (Second, _) = RoleValue.RowValue["point_native_ids"]
    FirstX, FirstY = Points[First]
    SecondX, SecondY = Points[Second]
    DeltaX, DeltaY = SecondX - FirstX, SecondY - FirstY
    if RoleValue.KindValue == "distance":
        Signed = Hypot(DeltaX, DeltaY)
    else:
        Signed = DeltaX if RoleValue.KindValue == "distance_x" else DeltaY
    RequireArch(
        abs(abs(Signed) - RoleValue.RowValue["metres"]) * 1000 <= KPointToleranceMm,
        True,
        "cut operand distance agrees with its saved scalar",
    )
    return Signed


# the rule preserves its stable public identities while adding exact operands and native provenance
def BuildCutDist(
    RuleValue: SketchRelation,
    RoleValue: CutDimRole,
    Source: CutRuleSource,
    Origin: CutOriginPoint,
    Lines: dict[int, CutRuleLine],
) -> SketchRelation:
    RequireArch(
        (RuleValue.references, RuleValue.suppressed),
        ((), False),
        "unresolved prior cut distance",
    )
    RowValue, SpanValue = RoleValue.RowValue, RoleValue.SpanValue
    (First, _), (Second, _) = RowValue["point_native_ids"]
    References = (
        MatchDistEdge(Lines, (First, Second))
        if RoleValue.Equation is None
        else CutOffsetRefs(RoleValue, Origin, Lines)
    )
    Signed = MeasureCutRule(RoleValue, Source)
    Provenance = RectSource(
        str(RowValue["native_id"]),
        Source.ConfigStream,
        SpanValue.Body,
        "sketch-distance",
    )
    Scalar = ProvenanceSpan(
        Source.ConfigStream, SpanValue.ScalarOffset, 8, "dimension-scalar"
    )
    return Replace(
        RuleValue,
        kind=RoleValue.KindValue,
        references=References,
        driving=RoleValue.Equation is None,
        provenance=Replace(Provenance, spans=(*Provenance.spans, Scalar)),
        attributes=FreezeMapping(
            {
                **RuleValue.attributes,
                "native_code": SpanValue.TypeCode,
                "native_distance_class": RowValue["class"],
                "native_dimension_id": RowValue["native_id"],
                "native_point_ids": tuple(RowValue["point_native_ids"]),
                "native_point_handles": tuple(RowValue["point_handle_objects"]),
                "solidworks.signed_distance_multiplier": -1 if Signed < 0 else 1,
            }
        ),
    )
