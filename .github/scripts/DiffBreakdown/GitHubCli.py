from __future__ import annotations

import json as JsonLib
import re as Regex
import subprocess as Subprocess
from pathlib import Path as FilePath


# the gh failure contract needs a dedicated boundary so published evidence stays bound to the reviewed revision
class GhFailure(RuntimeError):

    # the rate limited decision must stay consistent so published evidence stays bound to the reviewed revision
    def IsRateLimited(self) -> bool:
        MessageText = str(self).lower()
        return "rate limit" in MessageText or "http 429" in MessageText

    # the transient decision must stay consistent so published evidence stays bound to the reviewed revision
    def IsTransient(self) -> bool:
        return Regex.search(r"http 5\d\d", str(self).lower()) is not None


# the gh api operation needs one orchestration boundary so published evidence stays bound to the reviewed revision
def RunGhApi(*ArgList: str) -> str:
    ResultInfo = Subprocess.run(
        ["gh", "api", *ArgList],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if ResultInfo.returncode != 0:
        raise GhFailure(ResultInfo.stderr.strip() or "gh api failed")
    return ResultInfo.stdout


# the comment client contract needs a dedicated boundary so published evidence stays bound to the reviewed revision
class CommentClient:

    # comment client needs explicit initial state so published evidence stays bound to the reviewed revision
    def __init__(self, Repository: str, PullNumber: int) -> None:
        self.Endpoint = f"repos/{Repository}/issues/{PullNumber}/comments"

    # the list comments contract needs a shared interpretation so published evidence stays bound to the reviewed revision
    def ListComments(self) -> list[dict[str, object]]:
        PageText = RunGhApi("--paginate", "--slurp", f"{self.Endpoint}?per_page=100")
        return [Comment for PageList in JsonLib.loads(PageText) for Comment in PageList]

    # the post comment contract needs a shared interpretation so published evidence stays bound to the reviewed revision
    def PostComment(self, RequestPath: FilePath) -> int:
        ReplyText = RunGhApi(
            "--method", "POST", self.Endpoint, "--input", str(RequestPath)
        )
        return int(JsonLib.loads(ReplyText)["id"])
