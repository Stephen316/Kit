from dataclasses import dataclass as Dataclass, replace as Replace

from convert.adapters.solidworks.config.CutEquation import CutEquation
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.core.cut.CutRuleSource import CutRuleSource
from convert.adapters.solidworks.sketch.GeometryTypes import KPointId, KSketchDistance
from convert.adapters.solidworks.sketch.MemberSpans import DistanceSpan, MemberSpan
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.records.RecordParameter import Parameter
from interchange.records.RecordProvenance import ProvenanceSpan

# the saved distance subclass controls the local coordinate measured by each relation
KCutDistKinds = {
    "sgPntPntDist": "distance",
    "sgPntPntHorDist": "distance_x",
    "sgPntPntVertDist": "distance_y",
}


# equation target identities supply the role independently of names or display text
@Dataclass(frozen=True, slots=True)
class CutDimRole:
    RowValue: KSketchDistance
    SpanValue: DistanceSpan
    KindValue: str
    Equation: CutEquation | None


# each live dimension must have one equation operand or target at its exact saved slot
def ReadCutRoles(Source: CutRuleSource) -> dict[str, CutDimRole]:
    Targets = {Value.Target.DimensionSlot: Value for Value in Source.Equations}
    Inputs = {
        Value.InnerTerm.DimensionSlot: Value.InnerTerm for Value in Source.Equations
    }
    RequireArch(
        set(Targets) | set(Inputs),
        set(range(4)),
        "four independent cut dimension roles",
    )
    Shape = Source.SketchData
    SavedRows = zip(
        Shape.Geometry["length_dimensions"], Shape.Members.Distances, strict=True
    )
    Roles: dict[str, CutDimRole] = {}
    for SlotValue, (RowValue, SpanValue) in enumerate(SavedRows):
        Equation = Targets.get(SlotValue)
        TermValue = Equation.Target if Equation is not None else Inputs[SlotValue]
        RequireArch(
            (
                RowValue["native_id"],
                RowValue["name"],
                RowValue["metres"],
                Shape.Geometry["object_index"],
            ),
            (
                TermValue.DimensionId,
                TermValue.ParamName,
                TermValue.Metres,
                TermValue.SketchIndex,
            ),
            "same saved dimension and equation operand",
        )
        RequireArch(
            (SpanValue.TypeCode, SpanValue.ActivePair),
            (1, True),
            "active cut point pair",
        )
        KindValue = KCutDistKinds[RowValue["class"]]
        RequireArch(
            KindValue == "distance",
            Equation is None,
            "size or offset dimension class matches its role",
        )
        Roles[RowValue["name"]] = CutDimRole(RowValue, SpanValue, KindValue, Equation)
    RequireArch(len(Roles), 4, "four unique saved cut dimensions")
    return Roles


# the two dimensions of size and both offsets must meet at the same authored corner
def CheckRolePairs(Roles: dict[str, CutDimRole], OriginId: KPointId) -> None:
    First, Second = [Value for Value in Roles.values() if Value.Equation is None]
    FirstOffset, SecondOffset = [
        Value for Value in Roles.values() if Value.Equation is not None
    ]
    RequireArch(
        {FirstOffset.KindValue, SecondOffset.KindValue},
        {"distance_x", "distance_y"},
        "two saved local offset axes",
    )
    Common = set(First.RowValue["point_native_ids"]) & set(
        Second.RowValue["point_native_ids"]
    )
    RequireArch(len(Common), 1, "cut driving sizes share one vertex")
    RequireArch(
        FirstOffset.RowValue["point_native_ids"],
        SecondOffset.RowValue["point_native_ids"],
        "same ordered cut offset operands",
    )
    RequireArch(
        set(FirstOffset.RowValue["point_native_ids"]),
        Common | {OriginId},
        "offsets reach the same corner as both sizes",
    )


# the existing parameter binding must identify exactly the same inputs and cached value
def CheckCutParam(
    ParamValue: Parameter, RoleValue: CutDimRole, Source: CutRuleSource
) -> None:
    RequireArch(
        (ParamValue.value.kind, ParamValue.value.unit, ParamValue.value.value),
        (ValueKind.KLength, "mm", RoleValue.RowValue["metres"] * 1000),
        "cut parameter has the saved canonical length",
    )
    Equation = RoleValue.Equation
    if Equation is None:
        RequireArch(
            (ParamValue.role, ParamValue.expression),
            (ParameterRole.KDriving, None),
            "independent cut size parameter",
        )
        return
    Expression = ParamValue.expression
    if Expression is None:
        raise ValueError("Cut dimension equation has no bound expression")
    FirstId = f"sldprt:parameter:{Source.OuterProfileId}:{Equation.OuterTerm.ParamName}"
    SecondId = f"sldprt:parameter:{Source.ProfileId}:{Equation.InnerTerm.ParamName}"
    _, _, Right = Equation.SourceText.partition(" = ")
    RequireArch(
        (
            ParamValue.role,
            Expression.language,
            Expression.source,
            Expression.parameter_ids,
        ),
        (ParameterRole.KDerived, "solidworks", Right, (FirstId, SecondId)),
        "same ordered saved equation inputs",
    )
    Origin = ParamValue.provenance
    RequireArch(
        Origin is not None
        and any(
            SpanValue
            == ProvenanceSpan(
                Source.ConfigStream,
                Equation.Target.SlotOffset,
                4,
                "equation-target-slot",
            )
            for SpanValue in Origin.spans
        ),
        True,
        "equation provenance identifies the same target slot",
    )


# derived parameter provenance must keep its equation as well as the typed cached scalar
def KeepCutScalar(
    ParamValue: Parameter, RoleValue: CutDimRole, StreamName: str
) -> Parameter:
    ValueOffset = RoleValue.SpanValue.ScalarOffset
    Scalar = ProvenanceSpan(StreamName, ValueOffset, 8, "dimension-scalar")
    Origin = ParamValue.provenance
    if RoleValue.Equation is None or Origin is None:
        Origin = RectSource(
            str(RoleValue.RowValue["native_id"]),
            StreamName,
            MemberSpan(ValueOffset, ValueOffset + 8),
            Scalar.record_kind,
        )
    else:
        Origin = Replace(Origin, spans=Origin.spans + (Scalar,))
    return Replace(ParamValue, provenance=Origin)
