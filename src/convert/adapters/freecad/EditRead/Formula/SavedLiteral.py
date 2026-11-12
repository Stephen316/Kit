from dataclasses import replace as Replace

from convert.adapters.freecad.EditRead.Formula.SavedQuantity import KeepQuantity
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralExpr,
    ReadFormula,
)
from interchange.records.RecordParameter import Parameter


# only editable literal leaves may change their authored text or typed value
def ReadSavedLeaf(Param: Parameter, SavedText: str) -> Parameter:
    Expression = Param.expression
    Source = None if Expression is None else ReadFormula(Expression.source)
    Saved = ReadFormula(SavedText)
    if (
        Expression is None
        or Source is None
        or Saved is None
        or not IsLiteralExpr(Source)
        or not IsLiteralExpr(Saved)
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet input is not a supported literal"
        )
    OldValue, NewValue = EvalFormula(Source, {}), EvalFormula(Saved, {})
    if OldValue is None or NewValue is None:
        raise ValueError("FreeCAD editable spreadsheet literal could not be evaluated")
    if OldValue == NewValue:
        return Param
    return Replace(
        Param,
        value=KeepQuantity(Param.value, NewValue),
        expression=Replace(Expression, source=SavedText),
    )
