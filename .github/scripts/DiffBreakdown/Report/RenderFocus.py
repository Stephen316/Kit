from __future__ import annotations

from Report.MarkdownText import EscapeText

KShareNote = (
    "The bar follows the table order. Shares use additions + deletions and reconcile "
    "to 100% when text changes exist. Binary files have no fabricated line counts."
)


def RenderFocus(Snapshot: dict[str, object], Threshold: int) -> list[str]:
    Totals = Snapshot["Totals"]
    RowList = [
        "",
        KShareNote,
        "",
        "### Review focus",
        "",
        f"{Totals['Reviewable']:,} reviewable lines; {Totals['Excluded']:,} lines "
        "excluded by configured policy. This metric is not a guarantee of low risk.",
    ]
    if Totals["Reviewable"] > Threshold:
        RowList += [
            f"Review size exceeds the configured {Threshold:,}-line threshold; "
            "consider splitting the PR."
        ]
    Risks = sorted(
        {RiskText for FileItem in Snapshot["Files"] for RiskText in FileItem["Risks"]}
    )
    RowList += [""] if Risks else []
    RowList += [f"- {EscapeText(RiskText)}" for RiskText in Risks]
    Matched = Totals["Files"] - Totals["Unclassified"]
    return RowList + [
        "",
        f"Classification: {Matched:,} files matched deterministic rules or Git "
        f"metadata; **{Totals['Unclassified']:,} unclassified files remain "
        "reviewable**. Rule matches express configuration confidence, not semantic "
        "or security certainty.",
    ]
