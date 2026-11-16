from dataclasses import replace as Replace

from convert.Geometry.Formula.Arithmetic import EvalFormula, IsLiteralExpr, ReadFormula
from convert.Geometry.Formula.FormulaUnits import IsMatchingQty
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Sketch import Sketch, SketchRelation
from interchange.Records.RecordParameter import Parameter
from interchange.Records.RecordProvenance import ProvenanceSpan


# a named earlier driving dimension must corroborate the dependent cached quantity
def BindCenterExpr(
    Center: SketchRelation,
    BossSketch: Sketch,
    Params: dict[str, Parameter],
    Spans: tuple[ProvenanceSpan, ...],
) -> Parameter:
    ParameterData = Params.get(Center.parameter_id or "")
    if (
        ParameterData is None
        or ParameterData.provenance is None
        or ParameterData.expression is None
    ):
        raise ValueError("Fusion Cut center has no owned expression operand")
    Expression = ParameterData.expression
    Formula = ReadFormula(Expression.source)
    if Expression.parameter_ids or Formula is None or len(Formula.Names) != 1:
        raise ValueError("Unsupported Fusion Cut center parameter expression")
    (NameValue,) = Formula.Names
    DriverRows = tuple(
        (Value, Param)
        for Value in BossSketch.constraints
        if Value.kind == Center.kind
        and Value.driving
        and Value.parameter_id is not None
        and (Param := Params.get(Value.parameter_id)) is not None
        and Param.name == NameValue
    )
    if len(DriverRows) != 1 or Expression.source != f"{NameValue} / 2":
        raise ValueError(
            "Fusion center expression lacks a unique matching boss dimension"
        )
    ((Relation, Driver),) = DriverRows
    Cached = EvalFormula(Formula, {NameValue: Driver.value})
    DriverFormula = (
        None if Driver.expression is None else ReadFormula(Driver.expression.source)
    )
    if (
        Center.provenance is None
        or Relation.provenance is None
        or Cached is None
        or not IsMatchingQty(Cached, ParameterData.value)
        or DriverFormula is None
        or not IsLiteralExpr(DriverFormula)
    ):
        raise ValueError(
            "Fusion center expression and measured dimension roles disagree"
        )
    Origin = ParameterData.provenance
    return Replace(
        ParameterData,
        expression=Replace(Expression, parameter_ids=(Driver.id,)),
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + Spans
            + Center.provenance.spans
            + Relation.provenance.spans,
        ),
        attributes=FreezeMapping(
            {
                **ParameterData.attributes,
                "fusion.expression_binding": "scoped_dimension_registry",
            }
        ),
    )
