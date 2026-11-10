# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from decimal import Decimal, InvalidOperation

from convert.adapters.freecad.EditRead.PlaneRev.ExprParse import (
    KExprNode,
    ParsePlaneExpr,
)


# native saves can print writer literals at fifteen significant decimal digits
def IsSameNode(Expected: KExprNode, Actual: KExprNode) -> bool:
    if Expected == Actual:
        return True
    if not isinstance(Expected, tuple) or not isinstance(Actual, tuple):
        return False
    ExpectValue, ExpectUnit = Expected
    ActualValue, ActualUnit = Actual
    return (
        isinstance(ExpectValue, Decimal)
        and isinstance(ActualValue, Decimal)
        and ExpectUnit == ActualUnit
        and Decimal(format(float(ExpectValue), ".15g")) == ActualValue
    )


# the saved graph may change expression presentation without changing its operands
def IsSamePlaneExpr(Expected: str, Actual: str) -> bool:
    try:
        SourceNodes = ParsePlaneExpr(Expected)
        SavedNodes = ParsePlaneExpr(Actual)
    except (InvalidOperation, ValueError):
        return False
    return len(SourceNodes) == len(SavedNodes) and all(
        IsSameNode(SourceNode, SavedNode)
        for SourceNode, SavedNode in zip(SourceNodes, SavedNodes)
    )
