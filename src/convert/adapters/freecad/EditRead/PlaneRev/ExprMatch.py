# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
