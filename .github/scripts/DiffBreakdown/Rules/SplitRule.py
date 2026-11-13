from __future__ import annotations


def SplitRule(LineText: str) -> tuple[str, str]:
    for Index, CharText in enumerate(LineText):
        if CharText.isspace() and LineText[Index - 1 : Index] != "\\":
            PatternText = LineText[:Index].replace("\\ ", " ")
            return PatternText, LineText[Index:].strip()
    return LineText.replace("\\ ", " "), ""
