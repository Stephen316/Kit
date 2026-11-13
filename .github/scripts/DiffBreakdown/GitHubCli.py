from __future__ import annotations

import json as JsonLib
import re as Regex
import subprocess as Subprocess
from pathlib import Path as FilePath


class GhFailure(RuntimeError):
    def IsRateLimited(self) -> bool:
        MessageText = str(self).lower()
        return "rate limit" in MessageText or "http 429" in MessageText

    def IsTransient(self) -> bool:
        return Regex.search(r"http 5\d\d", str(self).lower()) is not None


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


class CommentClient:
    def __init__(self, Repository: str, PullNumber: int) -> None:
        self.Endpoint = f"repos/{Repository}/issues/{PullNumber}/comments"

    def ListComments(self) -> list[dict[str, object]]:
        PageText = RunGhApi("--paginate", "--slurp", f"{self.Endpoint}?per_page=100")
        return [Comment for PageList in JsonLib.loads(PageText) for Comment in PageList]

    def PostComment(self, RequestPath: FilePath) -> int:
        ReplyText = RunGhApi(
            "--method", "POST", self.Endpoint, "--input", str(RequestPath)
        )
        return int(JsonLib.loads(ReplyText)["id"])
