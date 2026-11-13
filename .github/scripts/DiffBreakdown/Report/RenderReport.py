from __future__ import annotations

from Report.RenderChanges import RenderChanges
from Report.RenderFiles import RenderFiles
from Report.RenderFocus import RenderFocus
from Report.RenderFooter import RenderFooter
from Report.RenderSummary import RenderSummary
from Rules.RuleSet import RuleSet

KCommentLimit = 60000


def RenderReport(
    Snapshot: dict[str, object],
    Rules: RuleSet,
    Previous: dict[str, object] | None,
    History: list[dict[str, object]],
) -> str:
    Config = Rules.Config
    RowList = RenderSummary(Snapshot, Previous is not None)
    RowList += RenderFocus(Snapshot, Config["ReviewThreshold"])
    RowList += RenderChanges(Snapshot, Previous) if Previous else []
    RowList += RenderFiles(Snapshot, Config["TopFiles"], Config["DetailFiles"])
    RowList += RenderFooter(Snapshot, History)
    BodyText = "\n".join(RowList) + "\n"
    if len(BodyText) > KCommentLimit:
        raise ValueError(
            "Report exceeds the GitHub comment budget; reduce categories or details"
        )
    return BodyText
