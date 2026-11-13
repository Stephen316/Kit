from __future__ import annotations

import hashlib as Hashlib
import json as JsonLib
from pathlib import Path as FilePath

KOutputPath = FilePath("DiffBreakdownResults")
KRequestPath = KOutputPath / "CommentRequest.json"


def WriteJson(TargetPath: FilePath, Value: object) -> None:
    KOutputPath.mkdir(parents=True, exist_ok=True)
    TargetPath.write_text(JsonLib.dumps(Value, indent=2, ensure_ascii=True) + "\n")


def WriteOutputs(Snapshot: dict[str, object], BodyText: str) -> dict[str, object]:
    KOutputPath.mkdir(parents=True, exist_ok=True)
    (KOutputPath / "Report.md").write_text(BodyText)
    WriteJson(KRequestPath, {"body": BodyText})
    Stored = {
        **Snapshot,
        "ReportSha": Hashlib.sha256(BodyText.encode()).hexdigest(),
        "CommentId": None,
        "Publication": "preview",
    }
    WriteJson(KOutputPath / "Snapshot.json", Stored)
    return Stored
