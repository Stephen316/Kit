from __future__ import annotations

import ast as AstLib


def IsIntValue(AstNode: AstLib.expr) -> bool:
    return (
        isinstance(AstNode, AstLib.Constant)
        and isinstance(AstNode.value, int)
        and not isinstance(AstNode.value, bool)
    )
