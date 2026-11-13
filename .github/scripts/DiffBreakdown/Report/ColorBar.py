from __future__ import annotations

from Report.MarkdownText import EscapeText
from Report.ShareCounts import ShareCounts

KTileUrl = "https://placehold.co/10x1000/{0}/{0}.png"
KEmptyBar = "No text-line changes; binary and metadata-only files are counted below."


def BarSegment(NameText: str, ColorText: str, Share: int) -> str:
    Width = f"{Share / 10:.1f}"
    return (
        f'<img src="{KTileUrl.format(ColorText)}" width="{Width}%" height="12" '
        f'alt="{EscapeText(NameText)}: {Width}%">'
    )


def ColorBar(Categories: dict[str, dict[str, object]]) -> str:
    Shares = ShareCounts(Categories)
    if not any(Shares.values()):
        return KEmptyBar
    Segments = [
        BarSegment(NameText, str(Categories[NameText]["Color"]), Share)
        for NameText, Share in Shares.items()
        if Share
    ]
    return "<p>" + "".join(Segments) + "</p>"
