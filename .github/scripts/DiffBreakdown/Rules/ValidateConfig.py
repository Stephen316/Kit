from __future__ import annotations

import re as Regex

KPolicyNames = frozenset({"review", "excluded", "separate"})
KNamePattern = r"[A-Za-z0-9][A-Za-z0-9 ()_/-]{0,63}"
KColorPattern = r"[0-9A-Fa-f]{6}"
KSizeLimits = (("TopFiles", 10), ("DetailFiles", 50), ("ReviewThreshold", 10**7))
KRoleKeys = ("Unknown", "Binary", "Formatting")


def RequireName(NameText: str) -> str:
    if Regex.fullmatch(KNamePattern, NameText) is None:
        raise ValueError(f"Invalid category name: {NameText!r}")
    return NameText


def ValidateConfig(Config: dict[str, object]) -> None:
    if Config.get("Version") != 1:
        raise ValueError("Unsupported diff breakdown configuration version")
    Categories = Config["Categories"]
    if not isinstance(Categories, dict) or not 1 <= len(Categories) <= 64:
        raise ValueError("Configure between 1 and 64 categories")
    for NameText, Settings in Categories.items():
        RequireName(NameText)
        if Settings["Policy"] not in KPolicyNames:
            raise ValueError(f"Invalid review policy for {NameText}")
        if Regex.fullmatch(KColorPattern, Settings["Color"]) is None:
            raise ValueError(f"Invalid color for {NameText}")
        if len(Settings.get("Risk", "")) > 200:
            raise ValueError("Risk descriptions must be at most 200 characters")
    for RoleKey in KRoleKeys:
        if Config[RoleKey] not in Categories:
            raise ValueError(f"Missing category for {RoleKey}")
    if Categories[Config["Unknown"]]["Policy"] != "review":
        raise ValueError("Unclassified files must remain reviewable")
    for LimitKey, Maximum in KSizeLimits:
        LimitValue = Config[LimitKey]
        if not isinstance(LimitValue, int) or isinstance(LimitValue, bool):
            raise ValueError(f"Invalid {LimitKey}")
        if not 1 <= LimitValue <= Maximum:
            raise ValueError(f"Invalid {LimitKey}")
