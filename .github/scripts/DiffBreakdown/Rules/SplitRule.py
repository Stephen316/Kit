from __future__ import annotations


# the split rule contract needs a stable decomposition so review categories remain consistent across push snapshots
def SplitRule(LineText: str) -> tuple[str, str]:
    for Index, CharText in enumerate(LineText):
        if CharText.isspace() and LineText[Index - 1 : Index] != "\\":
            PatternText = LineText[:Index].replace("\\ ", " ")
            return PatternText, LineText[Index:].strip()
    return LineText.replace("\\ ", " "), ""
