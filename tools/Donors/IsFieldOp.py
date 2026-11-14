from __future__ import annotations

import ast as AstLib
import re as Regex

from tools.Donors.IsIntValue import IsIntValue
from tools.Donors.ReplayRules import KKindPattern


def IsFieldOp(AstNode: AstLib.AST) -> bool:
    if not isinstance(AstNode, AstLib.Tuple) or len(AstNode.elts) < 4:
        return False
    KindNode = AstNode.elts[3]
    return (
        IsIntValue(AstNode.elts[0])
        and IsIntValue(AstNode.elts[1])
        and isinstance(KindNode, AstLib.Constant)
        and isinstance(KindNode.value, str)
        and Regex.fullmatch(KKindPattern, KindNode.value) is not None
    )
