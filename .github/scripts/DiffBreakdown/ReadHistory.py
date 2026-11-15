from __future__ import annotations

from SnapshotMarker import DecodeMarker
from ValidateRecord import IsValidRecord

# bot login must remain consistent across callers so published evidence stays bound to the reviewed revision
KBotLogin = "github-actions[bot]"


# the history operation needs a distinct decoding boundary so published evidence stays bound to the reviewed revision
def ReadHistory(
    Comments: list[dict[str, object]], Repository: str, PullNumber: int
) -> list[dict[str, object]]:
    History: list[dict[str, object]] = []
    for Comment in Comments:
        Author = Comment.get("user")
        if not isinstance(Author, dict) or Author.get("login") != KBotLogin:
            continue
        if Author.get("type") != "Bot":
            continue
        Record = DecodeMarker(str(Comment.get("body") or ""))
        if Record is None or not IsValidRecord(Record):
            continue
        if Record.get("Repository") != Repository or Record.get("Pull") != PullNumber:
            continue
        History.append({**Record, "CommentId": Comment["id"]})

    # ordering by run number entry comment id must stay deterministic so diff reporting resolves equivalent inputs consistently
    return sorted(History, key=lambda Entry: (Entry["RunNumber"], Entry["CommentId"]))


# find duplicate must resolve unambiguously so published evidence stays bound to the reviewed revision
def FindDuplicate(
    History: list[dict[str, object]], HeadSha: str
) -> dict[str, object] | None:
    return next((Entry for Entry in History if Entry["Head"] == HeadSha), None)


# the superseded decision must stay consistent so published evidence stays bound to the reviewed revision
def IsSuperseded(History: list[dict[str, object]], RunNumber: int) -> bool:
    return bool(History) and History[-1]["RunNumber"] > RunNumber
