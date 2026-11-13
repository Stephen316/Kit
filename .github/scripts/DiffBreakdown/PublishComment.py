from __future__ import annotations

import subprocess as Subprocess
import time as TimeLib
from pathlib import Path as FilePath

from GitHubCli import CommentClient, GhFailure
from ReadHistory import FindDuplicate, IsSuperseded, ReadHistory


def IsRetryable(ErrorInfo: Exception) -> bool:
    if isinstance(ErrorInfo, GhFailure):
        return ErrorInfo.IsTransient() and not ErrorInfo.IsRateLimited()
    return isinstance(ErrorInfo, Subprocess.TimeoutExpired)


def PublishComment(
    Client: CommentClient,
    Snapshot: dict[str, object],
    RequestPath: FilePath,
    History: list[dict[str, object]],
) -> tuple[int | None, str]:
    Repository, PullNumber = str(Snapshot["Repository"]), int(Snapshot["Pull"])
    Current = History
    for Attempt in range(3):
        if Attempt:
            TimeLib.sleep(Attempt)
            Current = ReadHistory(Client.ListComments(), Repository, PullNumber)
        Duplicate = FindDuplicate(Current, str(Snapshot["Head"]))
        if Duplicate is not None:
            return int(Duplicate["CommentId"]), "duplicate"
        if IsSuperseded(Current, int(Snapshot["RunNumber"])):
            return None, "superseded"
        try:
            return Client.PostComment(RequestPath), "published"
        except (GhFailure, Subprocess.TimeoutExpired) as ErrorInfo:
            if Attempt == 2 or not IsRetryable(ErrorInfo):
                raise
    raise RuntimeError("Comment publication exhausted retries")
