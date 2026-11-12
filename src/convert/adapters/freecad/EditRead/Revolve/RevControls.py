from math import degrees as Degrees, isclose as IsClose

from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditRead.XmlField import EditChild, EditFloat, EditScalar
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.VectorSpace import SpaceVector


# all persisted native vector components independently corroborate the selected origin axis
def CheckRevVector(Native: NativeObject, NameValue: str, Expected: SpaceVector) -> None:
    NodeValue = EditChild(Native, NameValue, "App::PropertyVector", "PropertyVector")
    if any(
        not IsClose(EditFloat(NodeValue, Field), Value, rel_tol=0.0, abs_tol=1e-9)
        for Field, Value in zip(
            ("valueX", "valueY", "valueZ"),
            (Expected.x, Expected.y, Expected.z),
            strict=True,
        )
    ):
        raise ValueError(f"FreeCAD editable Revolve {NameValue} changed")


# exact solver expressions and resolved native angles must describe the same saved sweep
def CheckRevValues(
    Native: NativeObject,
    PlanValue: EditRevolve,
    Expressions: tuple[tuple[str, str], ...],
    Along: float,
    Against: float | None,
) -> None:
    CheckRevVector(Native, "Axis", PlanValue.AxisDirection)
    CheckRevVector(Native, "Base", PlanValue.AxisOrigin)
    AxisLink = EditChild(Native, "AxisLink", "App::PropertyLinkSub", "LinkSub")
    if len(AxisLink) or AxisLink.attrib != {"value": "", "count": "0"}:
        raise ValueError("FreeCAD editable Revolve axis link changed")
    for Field, TypeName, TagName, Expected in (
        ("Solid", "App::PropertyBool", "Bool", "true"),
        (
            "Symmetric",
            "App::PropertyBool",
            "Bool",
            "true" if PlanValue.Symmetric else "false",
        ),
        ("FaceMakerClass", "App::PropertyString", "String", "Part::FaceMakerBullseye"),
    ):
        if EditScalar(Native, Field, TypeName, TagName) != Expected:
            raise ValueError(f"FreeCAD editable Revolve {Field} changed")
    Engine = EditChild(
        Native, "ExpressionEngine", "App::PropertyExpressionEngine", "ExpressionEngine"
    )
    if (
        not Expressions
        or len(Engine) != len(Expressions)
        or Engine.attrib != {"count": str(len(Expressions))}
        or any(
            RowValue.tag != "Expression"
            or len(RowValue)
            or RowValue.attrib != {"path": PathValue, "expression": Expression}
            for RowValue, (PathValue, Expression) in zip(
                Engine, Expressions, strict=True
            )
        )
    ):
        raise ValueError("FreeCAD editable Revolve expression binding changed")
    Actual = EditFloat(
        EditChild(Native, "Angle", "App::PropertyFloatConstraint", "Float"), "value"
    )
    ExpectedAngle = Degrees(Along if Against is None else Along + Against)
    if not IsClose(Actual, ExpectedAngle, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(
            "FreeCAD editable Revolve angle disagrees with its spreadsheet"
        )
