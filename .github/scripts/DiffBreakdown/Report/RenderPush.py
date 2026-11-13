from __future__ import annotations

from Report.MarkdownText import EscapeText
from SummarizeFiles import SummarizeFiles

KRewriteNote = (
    "The previous head is not an ancestor of this head: a force push, rebase, or "
    "history rewrite occurred. The push measurement compares the exact two trees."
)


def RenderPush(Snapshot: dict[str, object]) -> list[str]:
    RowList = ["", "### What changed in this push", ""]
    Closing = ["", "Net PR snapshot changes are not the lines edited during this push."]
    if Snapshot["PushLimit"]:
        return RowList + [EscapeText(Snapshot["PushLimit"], 500)] + Closing
    PushInfo = SummarizeFiles(Snapshot["PushFiles"])
    Totals = PushInfo["Totals"]
    RowList += [
        f"Actual head-to-head diff: **+{Totals['Additions']:,} / "
        f"−{Totals['Deletions']:,}** across **{Totals['Files']:,} files** "
        f"({Totals['Binary']:,} binary)."
    ]
    RowList += [
        f"- {EscapeText(NameText)}: {Values['Files']:,} files, "
        f"+{Values['Additions']:,} / −{Values['Deletions']:,}"
        for NameText, Values in PushInfo["Categories"].items()
    ]
    RowList += [KRewriteNote] if Snapshot["Rewritten"] else []
    return RowList + Closing
