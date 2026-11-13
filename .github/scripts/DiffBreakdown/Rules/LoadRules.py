from __future__ import annotations

import hashlib as Hashlib
from dataclasses import dataclass as DataClass

from Rules.SplitRule import SplitRule
from Rules.ValidateConfig import RequireName


@DataClass(frozen=True)
class RuleEntry:
    Pattern: str
    Label: str | None
    Source: str


def LoadRules(
    RulesText: str, Categories: dict[str, dict[str, str]]
) -> tuple[list[RuleEntry], dict[str, dict[str, str]]]:
    RuleList: list[RuleEntry] = []
    KnownNames = dict(Categories)
    for LineNumber, RawLine in enumerate(RulesText.splitlines(), 1):
        LineText = RawLine.strip()
        if not LineText or LineText.startswith("#"):
            continue
        PatternText, LabelText = SplitRule(LineText)
        IsReset = PatternText.startswith("!")
        PatternText = PatternText.removeprefix("!")
        if IsReset == bool(LabelText):
            raise ValueError(
                f"DiffRules.txt:{LineNumber}: rules need a category and resets take none"
            )
        if not 0 < len(PatternText) <= 512:
            raise ValueError(f"DiffRules.txt:{LineNumber}: invalid pattern length")
        if LabelText and LabelText not in KnownNames:
            ColorText = Hashlib.sha256(RequireName(LabelText).encode()).hexdigest()
            KnownNames[LabelText] = {"Policy": "review", "Color": ColorText[:6]}
        RuleList.append(RuleEntry(PatternText, LabelText or None, RawLine))
    if len(RuleList) > 256 or len(KnownNames) > 64:
        raise ValueError("DiffRules.txt supports at most 256 rules and 64 categories")
    return RuleList, KnownNames
