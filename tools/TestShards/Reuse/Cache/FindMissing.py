from __future__ import annotations

import json as JsonLib
from collections.abc import Sequence
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.ReadObject import ReadObject


def FindMissing(LogPaths: Sequence[FilePath]) -> list[str]:
    Missing: list[str] = []
    for LogPath in LogPaths:
        Workers: set[str] = set()
        for LineText in LogPath.read_text(encoding="utf-8").splitlines():
            Fields = (
                ReadObject(JsonLib.loads(LineText), LogPath.name) if LineText else {}
            )
            WorkerId = Fields.get("worker_id", "main")
            if Fields.get("$report_type") == "TestReport" and isinstance(WorkerId, str):
                Workers.add(WorkerId)
        DepPaths = [
            LogPath.parent / f"Deps-{WorkerId}.json" for WorkerId in sorted(Workers)
        ]
        Missing.extend(str(DepPath) for DepPath in DepPaths if not DepPath.is_file())
    return Missing
