from __future__ import annotations

from Report.ColorBar import ColorBar
from Report.MarkdownText import CommitLink, EscapeText
from Report.ShareCounts import CountLines, ExcludedShare, ShareCounts


def CategoryRow(NameText: str, Values: dict[str, object], Share: int) -> str:
    return (
        f"| {EscapeText(NameText)} | +{Values['Additions']:,} | −{Values['Deletions']:,} "
        f"| {CountLines(Values):,} | {Share / 10:.1f}% | {Values['Files']:,} "
        f"| {EscapeText(Values['Policy'])} |"
    )


def RenderSummary(Snapshot: dict[str, object], IsUpdate: bool) -> list[str]:
    Totals = Snapshot["Totals"]
    Categories = Snapshot["Categories"]
    TitleText = f"update #{Snapshot['Sequence']}" if IsUpdate else "initial analysis"
    Shares = ShareCounts(Categories)
    RowList = [
        "<details>",
        f"<summary>Diff intelligence · {TitleText} · {Totals['Lines']:,} changed lines "
        f"· {Totals['Reviewable']:,} reviewable</summary>",
        "",
        f"PR #{Snapshot['Pull']} · {CommitLink(Snapshot, Snapshot['Head'])}",
        "",
        "| Total PR diff | Reviewable | Excluded from review |",
        "| ---: | ---: | ---: |",
        f"| **{Totals['Lines']:,}** | **{Totals['Reviewable']:,}** "
        f"| **{ExcludedShare(Totals):.1f}%** |",
        "",
        f"+{Totals['Additions']:,} additions · −{Totals['Deletions']:,} deletions "
        f"· {Totals['Files']:,} files · {Totals['Binary']:,} binary files",
        "",
        ColorBar(Categories),
        "",
        "| Category | Additions | Deletions | Lines | Share | Files | Policy |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    return RowList + [
        CategoryRow(NameText, Values, Shares[NameText])
        for NameText, Values in Categories.items()
    ]
