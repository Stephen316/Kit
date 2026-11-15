from __future__ import annotations

import hashlib as Hashlib
import json as JsonLib
from pathlib import Path as FilePath

# output path needs a stable location so diff reporting resolves inputs independently of the caller working directory
KOutputPath = FilePath("DiffBreakdownResults")

# request path needs a stable location so diff reporting resolves inputs independently of the caller working directory
KRequestPath = KOutputPath / "CommentRequest.json"


# the json operation needs a consistent construction rule so published evidence stays bound to the reviewed revision
def WriteJson(TargetPath: FilePath, Value: object) -> None:
    KOutputPath.mkdir(parents=True, exist_ok=True)
    TargetPath.write_text(JsonLib.dumps(Value, indent=2, ensure_ascii=True) + "\n")


# the outputs operation needs a consistent construction rule so published evidence stays bound to the reviewed revision
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
