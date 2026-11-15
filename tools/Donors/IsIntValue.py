from __future__ import annotations

import ast as AstLib


# the int value decision must stay consistent so captured document data cannot become production writer input
def IsIntValue(AstNode: AstLib.expr) -> bool:
    return (
        isinstance(AstNode, AstLib.Constant)
        and isinstance(AstNode.value, int)
        and not isinstance(AstNode.value, bool)
    )
