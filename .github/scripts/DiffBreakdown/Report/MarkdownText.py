from __future__ import annotations

import html as HtmlLib
from urllib.parse import quote as QuoteUrl

KMarkdownChars = frozenset("\\`*_{}[]()#+-.!|@<>\n\r")


def EscapeText(Value: object, Limit: int = 240) -> str:
    Clipped = str(Value)
    if len(Clipped) > Limit:
        Clipped = Clipped[:Limit] + "…"
    return "".join(
        (
            f"&#{ord(CharText)};"
            if CharText in KMarkdownChars
            else HtmlLib.escape(CharText)
        )
        for CharText in Clipped
    )


def CommitLink(Snapshot: dict[str, object], CommitSha: object) -> str:
    ShaText = str(CommitSha)
    return f"[`{ShaText[:10]}`](https://github.com/{Snapshot['Repository']}/commit/{ShaText})"


def FileLink(Snapshot: dict[str, object], FileItem: dict[str, object]) -> str:
    CommitSha = Snapshot["MergeBase"] if FileItem["Status"] == "D" else Snapshot["Head"]
    PathText = str(FileItem["Path"])
    Location = QuoteUrl(PathText, safe="/", errors="replace")
    BlobUrl = f"https://github.com/{Snapshot['Repository']}/blob/{CommitSha}/{Location}"
    return f"[{EscapeText(PathText)}]({BlobUrl})"
