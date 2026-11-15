from __future__ import annotations

import html as HtmlLib
from urllib.parse import quote as QuoteUrl

# the markdown chars vocabulary must stay centralized so diff reporting agrees on supported native identities
KMarkdownChars = frozenset("\\`*_{}[]()#+-.!|@<>\n\r")


# the escape text contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
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


# the commit link contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def CommitLink(Snapshot: dict[str, object], CommitSha: object) -> str:
    ShaText = str(CommitSha)
    return f"[`{ShaText[:10]}`](https://github.com/{Snapshot['Repository']}/commit/{ShaText})"


# the file link contract needs a shared interpretation so reviewers can distinguish semantic changes from generated noise
def FileLink(Snapshot: dict[str, object], FileItem: dict[str, object]) -> str:
    CommitSha = Snapshot["MergeBase"] if FileItem["Status"] == "D" else Snapshot["Head"]
    PathText = str(FileItem["Path"])
    Location = QuoteUrl(PathText, safe="/", errors="replace")
    BlobUrl = f"https://github.com/{Snapshot['Repository']}/blob/{CommitSha}/{Location}"
    return f"[{EscapeText(PathText)}]({BlobUrl})"
