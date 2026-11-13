from __future__ import annotations

import hashlib as Hashlib
import json as JsonLib

from Rules.GlobMatch import IsGlobMatch
from Rules.LoadRules import LoadRules
from Rules.ValidateConfig import ValidateConfig


class RuleSet:
    def __init__(self, RulesText: str, ConfigText: str) -> None:
        self.Config = JsonLib.loads(ConfigText)
        ValidateConfig(self.Config)
        self.Rules, self.Categories = LoadRules(RulesText, self.Config["Categories"])
        SourceText = f"{RulesText}\0{ConfigText}"
        self.Version = Hashlib.sha256(SourceText.encode()).hexdigest()

    def Classify(
        self, PathText: str, IsBinary: bool = False, IsSpacing: bool = False
    ) -> dict[str, object]:
        LabelText = self.Config["Unknown"]
        Matched = None
        RiskSet: set[str] = set()
        for RuleItem in self.Rules:
            if not IsGlobMatch(RuleItem.Pattern, PathText):
                continue
            LabelText = RuleItem.Label or self.Config["Unknown"]
            Matched = RuleItem.Source if RuleItem.Label else None
            RiskSet |= {self.Categories[LabelText].get("Risk", "")}
        if IsBinary or IsSpacing:
            LabelText = self.Config["Binary" if IsBinary else "Formatting"]
        Settings = self.Categories[LabelText]
        RiskSet |= {Settings.get("Risk", "")}
        return {
            "Category": LabelText,
            "Policy": Settings["Policy"],
            "Color": Settings["Color"],
            "Rule": Matched,
            "Confidence": self.RateMatch(Matched, IsBinary, IsSpacing),
            "Risks": sorted(RiskSet - {""}),
        }

    @staticmethod
    def RateMatch(Matched: str | None, IsBinary: bool, IsSpacing: bool) -> str:
        if IsBinary or IsSpacing:
            return "binary" if IsBinary else "whitespace"
        return "configured" if Matched else "unclassified"
