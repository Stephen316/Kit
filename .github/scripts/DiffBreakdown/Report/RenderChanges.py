from __future__ import annotations

from Report.MarkdownText import CommitLink, EscapeText
from Report.RenderPush import RenderPush
from Report.ShareCounts import CountLines, ExcludedShare

# rules note must remain consistent across callers so reviewers can distinguish semantic changes from generated noise
KRulesNote = (
    "Classification rules changed since the previous report; composition deltas "
    "include reclassification."
)

# base note must remain consistent across callers so reviewers can distinguish semantic changes from generated noise
KBaseNote = "The merge base changed; snapshot deltas also reflect the updated base."


# the render changes contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def RenderChanges(
    Snapshot: dict[str, object], Previous: dict[str, object]
) -> list[str]:
    Totals, OldTotals = Snapshot["Totals"], Previous["Totals"]
    Shift = ExcludedShare(Totals) - ExcludedShare(OldTotals)
    RowList = [
        "",
        "### Composition changes",
        "",
        f"Previous {CommitLink(Snapshot, Previous['Head'])} → current "
        f"{CommitLink(Snapshot, Snapshot['Head'])}",
        "",
        f"Net snapshot change: **{Totals['Lines'] - OldTotals['Lines']:+,} total "
        f"lines**, **{Totals['Reviewable'] - OldTotals['Reviewable']:+,} reviewable "
        f"lines**, **{Shift:+.1f} percentage points excluded**.",
        "",
        "| Category | Previous | Current | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for NameText in sorted({*Snapshot["Categories"], *Previous["Categories"]}):
        Before = CountLines(Previous["Categories"].get(NameText, {}))
        After = CountLines(Snapshot["Categories"].get(NameText, {}))
        RowList += [
            f"| {EscapeText(NameText)} | {Before:,} | {After:,} | {After - Before:+,} |"
        ]
    if Previous["RulesVersion"] != Snapshot["RulesVersion"]:
        RowList += ["", KRulesNote]
    if Previous["MergeBase"] != Snapshot["MergeBase"]:
        RowList += ["", KBaseNote]
    return RowList + RenderPush(Snapshot)
