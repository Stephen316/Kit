# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import re as Regex


# frontmatter removal preserves rule bodies while omitting source specific metadata
def StripSource(SourceText: str) -> str:
    MatchInfo = Regex.match(r"\A---\r?\n[\s\S]*?\r?\n---\r?\n?", SourceText)
    if MatchInfo:
        SourceText = SourceText[MatchInfo.end() :].lstrip("\r\n")
    return SourceText.rstrip() + "\n"
