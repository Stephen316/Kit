# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from collections.abc import Sequence

from convert.adapters.freecad.EditRead.PlaneRev.ExprMatch import IsSamePlaneExpr
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject


# native expression normalization may only change syntax and numeric serialization
def CheckPlaneExpr(Native: NativeObject, Expected: Sequence[tuple[str, str]]) -> None:
    Engine = EditChild(
        Native, "ExpressionEngine", "App::PropertyExpressionEngine", "ExpressionEngine"
    )
    if (
        len(Engine) != len(Expected)
        or Engine.attrib != {"count": str(len(Expected))}
        or any(
            Value.tag != "Expression"
            or len(Value)
            or set(Value.attrib) != {"path", "expression"}
            or Value.get("path") != PathValue
            or not IsSamePlaneExpr(TextValue, Value.get("expression", ""))
            for Value, (PathValue, TextValue) in zip(Engine, Expected, strict=True)
        )
    ):
        raise ValueError(
            f"FreeCAD editable plane Revolve {Native.name} expression binding changed"
        )
