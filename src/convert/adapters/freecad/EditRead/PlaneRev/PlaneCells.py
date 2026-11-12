from xml.etree.ElementTree import Element

from convert.adapters.freecad.Archive import Items, ParamCatalog
from convert.adapters.freecad.EditPlaneRev.PlaneRevPlan import PlaneRevPlan
from convert.adapters.freecad.EditRead.Revolve.RevSheet import (
    ReadRevCells,
    ReadRevLiteral,
)
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Formula.Arithmetic import (
    EvalFormula,
    IsLiteralExpr,
    ReadFormula,
)
from convert.geometry.Formula.FormulaUnits import GetQuantity
from interchange.records.RecordParameter import Parameter
from interchange.serialization.EncodeData import ToData


# archived offset and along cells are protected even when native spelling changes
def CheckInertCell(NodeValue: Element, Original: Parameter) -> None:
    Content = NodeValue.get("content", "")
    Formula = ReadFormula(Content[1:]) if Content.startswith("=") else None
    if Formula is None or not IsLiteralExpr(Formula):
        raise ValueError(
            "FreeCAD editable plane Revolve inactive control is not a literal"
        )
    Quantity = EvalFormula(Formula, {})
    if Quantity is None or Quantity != GetQuantity(Original.value):
        raise ValueError("FreeCAD editable plane Revolve inactive control changed")


# cell aliases preserve native parameter identity and only datum angles can drive a saved edit
def ReadPlaneCells(
    Sheet: NativeObject, Parameters: tuple[Parameter, ...], PlanValue: PlaneRevPlan
) -> tuple[dict[str, str], dict[str, tuple[float, str]]]:
    Aliases = ParamCatalog(Items(ToData(Parameters))).Aliases
    Cells = ReadRevCells(Sheet, Parameters, Aliases)
    ByParam = {Param.id: Param for Param in Parameters}
    for Identity in (
        PlanValue.InactiveParamId,
        *(Target.OffsetParamId for Target in PlanValue.Targets),
    ):
        CheckInertCell(Cells[Aliases[Identity]], ByParam[Identity])
    return Aliases, {
        Target.AngleParamId: ReadRevLiteral(
            Cells[Aliases[Target.AngleParamId]].get("content", ""),
            ByParam[Target.AngleParamId],
        )
        for Target in PlanValue.Targets
    }
