from dataclasses import replace as Replace

from convert.adapters.freecad.EditRead.Formula.SavedFormula import IsSameFormula
from convert.adapters.freecad.EditRead.Formula.SavedQuantity import KeepQuantity
from convert.adapters.freecad.FormulaSheet.FormulaPlans import (
    FormulaPlan,
    ReadFormulaRefs,
)
from convert.geometry.Formula.Arithmetic import EvalFormula, ReadFormula
from convert.geometry.Formula.FormulaUnits import IsMatchingQty
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import Parameter, ParameterValue


# a retained native operator tree must evaluate through exactly its declared inputs
def EvalSavedRow(
    Param: Parameter,
    PlanValue: FormulaPlan,
    SavedText: str,
    Current: dict[str, Parameter],
    Aliases: dict[str, str],
    Changes: set[str],
    DepthMm: float | None,
) -> Parameter:
    Expression = Param.expression
    Source = None if Expression is None else ReadFormula(Expression.source)
    Expected, Saved = ReadFormula(PlanValue.Content), ReadFormula(SavedText)
    if (
        Source is None
        or Expected is None
        or Saved is None
        or not IsSameFormula(Expected, Saved)
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet formula structure or aliases changed"
        )
    Inputs = ReadFormulaRefs(Source.Names, PlanValue.References, Current, Aliases)
    Quantity = None if Inputs is None else EvalFormula(Source, Inputs[0])
    if Quantity is None:
        raise ValueError("FreeCAD editable spreadsheet formula could not be evaluated")
    if DepthMm is not None:
        if not IsMatchingQty(
            Quantity, ParameterValue(value=DepthMm, kind=ValueKind.KLength, unit="mm")
        ):
            raise ValueError(
                "FreeCAD editable spreadsheet formula disagrees with saved LengthFwd"
            )
        Quantity = (DepthMm, (1, 0))
    if Changes.isdisjoint(PlanValue.References):
        if not IsMatchingQty(Quantity, Param.value):
            raise ValueError(
                "FreeCAD editable spreadsheet unchanged formula quantity disagrees"
            )
        return Param
    Updated = KeepQuantity(Param.value, Quantity)
    return Param if Updated is Param.value else Replace(Param, value=Updated)
