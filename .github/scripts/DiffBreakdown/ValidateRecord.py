from __future__ import annotations

import re as Regex

from SummarizeFiles import KTotalKeys

# the sha keys order must stay explicit so published evidence stays bound to the reviewed revision
KShaKeys = ("Base", "Head", "MergeBase")

# count keys needs one explicit bound so diff reporting cannot accept inconsistent resource or layout limits
KCountKeys = ("Files", "Binary", "Additions", "Deletions")

# the integer keys order must stay explicit so published evidence stays bound to the reviewed revision
KIntegerKeys = ("RunNumber", "RunId", "Sequence")


# the count decision must stay consistent so published evidence stays bound to the reviewed revision
def IsCount(Value: object) -> bool:
    return (
        isinstance(Value, int) and not isinstance(Value, bool) and 0 <= Value <= 10**12
    )


# the valid record decision must stay consistent so published evidence stays bound to the reviewed revision
def IsValidRecord(Record: dict[str, object]) -> bool:
    Totals, Categories = Record.get("Totals"), Record.get("Categories")
    if not isinstance(Totals, dict) or not isinstance(Categories, dict):
        return False
    if len(Categories) > 64 or not isinstance(Record.get("RulesVersion"), str):
        return False
    if not all(isinstance(Record.get(KeyText), str) for KeyText in KShaKeys):
        return False
    if not all(
        Regex.fullmatch(r"[0-9a-f]{40}", Record[KeyText]) for KeyText in KShaKeys
    ):
        return False
    if not all(IsCount(Record.get(KeyText)) for KeyText in KIntegerKeys):
        return False
    if not all(IsCount(Totals.get(KeyText)) for KeyText in KTotalKeys):
        return False
    return all(
        isinstance(Values, dict) and IsCount(Values.get(KeyText))
        for Values in Categories.values()
        for KeyText in KCountKeys
    )
