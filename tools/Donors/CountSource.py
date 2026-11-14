from __future__ import annotations

import ast as AstLib

from tools.Donors.IsFieldOp import IsFieldOp
from tools.Donors.IsReplayCall import IsReplayCall


def CountSource(SourceText: str, FileName: str) -> tuple[int, int]:
    SyntaxTree = AstLib.parse(SourceText, filename=FileName)
    FieldTotal = 0
    CallTotal = 0
    for AstNode in AstLib.walk(SyntaxTree):
        if IsFieldOp(AstNode):
            FieldTotal += 1
        elif IsReplayCall(AstNode):
            CallTotal += 1
    return FieldTotal, CallTotal
