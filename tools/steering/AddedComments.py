# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections import Counter
from io import StringIO
from pathlib import Path as FilePath
from tokenize import COMMENT, generate_tokens as GenerateTokens
from tools.steering.SteeringCompliance import (
    Finding,
    IsHeaderComment,
    IsPragmaComment,
)


def AddedComments(SourcePath: FilePath, BaseText: str, HeadText: str) -> list[Finding]:
    Prior = Counter(
        TokenInfo.string
        for TokenInfo in GenerateTokens(StringIO(BaseText).readline)
        if TokenInfo.type == COMMENT
    )
    Findings: list[Finding] = []
    StartLine = 2 if HeadText.startswith("#!") else 1
    for TokenInfo in GenerateTokens(StringIO(HeadText).readline):
        if TokenInfo.type != COMMENT:
            continue
        if IsHeaderComment(TokenInfo, StartLine) or IsPragmaComment(TokenInfo):
            continue
        if Prior[TokenInfo.string] > 0:
            Prior[TokenInfo.string] -= 1
            continue
        Findings.append(
            Finding(
                SourcePath,
                TokenInfo.start[0],
                TokenInfo.start[1] + 1,
                "CMT002",
                "new explanatory code comments are prohibited",
            )
        )
    return Findings
