from __future__ import annotations


def CountLines(Values: dict[str, object]) -> int:
    return int(Values.get("Additions", 0)) + int(Values.get("Deletions", 0))


def ExcludedShare(Totals: dict[str, object]) -> float:
    LineTotal = int(Totals["Lines"])
    return int(Totals["Excluded"]) * 100 / LineTotal if LineTotal else 0.0


def ShareCounts(Categories: dict[str, dict[str, object]]) -> dict[str, int]:
    Counts = {NameText: CountLines(Values) for NameText, Values in Categories.items()}
    Total = sum(Counts.values())
    if not Total:
        return dict.fromkeys(Counts, 0)
    Shares = {NameText: Count * 1000 // Total for NameText, Count in Counts.items()}
    Ordered = sorted(
        Counts, key=lambda NameText: (-(Counts[NameText] * 1000 % Total), NameText)
    )
    Raised = set(Ordered[: 1000 - sum(Shares.values())])
    return {
        NameText: Share + int(NameText in Raised) for NameText, Share in Shares.items()
    }
