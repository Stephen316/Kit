from collections import Counter
from dataclasses import replace as Replace

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.DimRuleProjection import ProjectDimRules
from convert.Formats.Fusion.Sketches.GeomRuleProjection import BuildGeomRules
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.Enums.EnumValues import ParameterRole
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Parameter


# sketch records retain both geometric intent and exact dimensional parameter links
def AttachRules(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Sketches: tuple[Sketch, ...],
    Parameters: tuple[Parameter, ...],
) -> tuple[tuple[Sketch, ...], tuple[Diagnostic, ...]]:
    if not Sketches:
        return Sketches, ()
    Geometric, GeomIssues = BuildGeomRules(BulkData, Spans, Sketches)
    Dimensional, DimIssues = ProjectDimRules(BulkData, Spans, Sketches, Parameters)
    Result: list[Sketch] = []
    for SketchValue in Sketches:
        DimRules = Dimensional.get(SketchValue.id, ())
        Rules = Geometric.get(SketchValue.id, ()) + DimRules
        if Rules:
            DimParams = tuple(
                Value.parameter_id for Value in DimRules if Value.parameter_id
            )
            SketchValue = Replace(
                SketchValue,
                constraints=Rules,
                parameter_ids=tuple(
                    dict.fromkeys(SketchValue.parameter_ids + DimParams)
                ),
            )
        Result.append(SketchValue)
    return tuple(Result), GeomIssues + DimIssues


# only a successfully bound circular rule establishes an editable dimension parameter
def PromoteCirDrive(
    Sketches: tuple[Sketch, ...],
    Parameters: tuple[Parameter, ...],
    Issues: tuple[Diagnostic, ...],
) -> tuple[Parameter, ...]:
    Unqualified = {
        IssueValue.entity_id
        for IssueValue in Issues
        if IssueValue.code.startswith("fusion.sketch.dimension.")
    }
    UsesByParam = Counter(
        RuleValue.parameter_id
        for SketchValue in Sketches
        for RuleValue in SketchValue.constraints
    )
    DrivingIds = {
        RuleValue.parameter_id
        for SketchValue in Sketches
        if SketchValue.id not in Unqualified
        for RuleValue in SketchValue.constraints
        if RuleValue.driving is True
        and RuleValue.kind
        in (ConstraintKind.KDiameter.value, ConstraintKind.KRadius.value)
        and UsesByParam[RuleValue.parameter_id] == 1
    }
    if not DrivingIds:
        return Parameters
    return tuple(
        (
            Replace(ParamValue, role=ParameterRole.KDriving)
            if ParamValue.id in DrivingIds
            and ParamValue.role is ParameterRole.KReference
            else ParamValue
        )
        for ParamValue in Parameters
    )
