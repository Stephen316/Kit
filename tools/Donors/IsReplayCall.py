from __future__ import annotations

import ast as AstLib

from tools.Donors.ReplayRules import KReplayNames


def IsReplayCall(AstNode: AstLib.AST) -> bool:
    if not isinstance(AstNode, AstLib.Call):
        return False
    FuncNode = AstNode.func
    if isinstance(FuncNode, AstLib.Name):
        return FuncNode.id in KReplayNames
    if isinstance(FuncNode, AstLib.Attribute):
        return FuncNode.attr in KReplayNames
    return False
