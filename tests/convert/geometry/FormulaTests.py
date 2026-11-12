from pytest import approx as Approx, mark as MarkTest

from convert.geometry.Formula.Arithmetic import EvalFormula, ReadFormula, WriteFormula
from convert.geometry.Formula.FormulaUnits import IsMatchingQty
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import ParameterValue


# literal units and name bindings must stay exact through evaluation and emission
def TestExprUnits() -> None:
    FormulaValue = ReadFormula("probe + probeWidth * 2 + probeWidth / 2 - 1e-1 cm")
    assert FormulaValue is not None
    assert FormulaValue.Names == ("probe", "probeWidth")
    Values = {
        "probe": ParameterValue(1.0, ValueKind.KLength, "in"),
        "probeWidth": ParameterValue(0.4, ValueKind.KLength, "cm"),
    }
    Result = EvalFormula(FormulaValue, Values)
    assert Result is not None and Result[0] == Approx(34.4)
    assert IsMatchingQty(Result, ParameterValue(3.44, ValueKind.KLength, "cm"))
    assert not IsMatchingQty(Result, ParameterValue(34.4))
    assert WriteFormula(
        FormulaValue, {"probe": "first_alias", "probeWidth": "second_alias"}
    ) == ("first_alias + second_alias * 2 + second_alias / 2 - 1e-1 cm")
    assert (
        WriteFormula(FormulaValue, {"probe": "same_alias", "probeWidth": "same_alias"})
        is None
    )


# partial expression matches must never emit functions references or unsupported operators
@MarkTest.parametrize(
    "Source",
    ("sqrt(width)", "x.y", "a // 2", "a ^ 2", "a; b", "a\n+ b", "1e999 mm", "pi + 1"),
)
def TestBadFormula(Source: str) -> None:
    assert ReadFormula(Source) is None


# invalid units and missing values cannot be flattened into a plausible scalar
@MarkTest.parametrize(
    "Source", ("width + 1", "width / 0", "missing + 1 mm", "width * 1e308")
)
def TestBadMeasure(Source: str) -> None:
    FormulaValue = ReadFormula(Source)
    assert FormulaValue is not None
    assert (
        EvalFormula(
            FormulaValue, {"width": ParameterValue(10.0, ValueKind.KLength, "mm")}
        )
        is None
    )
