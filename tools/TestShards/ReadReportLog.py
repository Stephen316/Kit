from __future__ import annotations

import json as JsonLib
from pathlib import Path as FilePath
from typing import cast as CastValue

from tools.TestShards.ParsePhase import ParsePhase
from tools.TestShards.PhaseReport import PhaseReport
from tools.TestShards.ShardLog import ShardLog


def ReadReportLog(LogPath: FilePath) -> ShardLog:
    Phases: list[PhaseReport] = []
    Finished = False
    for LineText in LogPath.read_text(encoding="utf-8").splitlines():
        if not LineText.strip():
            continue
        Decoded: object = JsonLib.loads(LineText)
        if not isinstance(Decoded, dict):
            raise ValueError(f"{LogPath} contains a line that is not an object")
        Fields = CastValue(dict[object, object], Decoded)
        ReportType = Fields.get("$report_type")
        Finished = Finished or ReportType == "SessionFinish"
        if ReportType == "TestReport":
            Phases.append(ParsePhase(Fields))
    return ShardLog(tuple(Phases), Finished)
