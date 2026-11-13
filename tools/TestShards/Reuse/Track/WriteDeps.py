from __future__ import annotations

import json as JsonLib
import platform as Platform
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Track.TrackState import TrackState


def WriteDeps(State: TrackState, OutDir: FilePath, Worker: str) -> None:
    Payload = {
        "Worker": Worker,
        "Python": Platform.python_version(),
        "Failures": State.Failures,
        "Modules": {
            ModKey: {
                "Files": sorted(Record.Files),
                "Folders": sorted(Record.Folders),
                "Opaque": Record.Opaque,
            }
            for ModKey, Record in sorted(State.Modules.items())
        },
        "Links": {
            Source: sorted(Targets) for Source, Targets in sorted(State.Links.items())
        },
        "Listers": {
            Source: sorted(Targets) for Source, Targets in sorted(State.Listers.items())
        },
        "Spawners": sorted(State.Spawners),
    }
    OutDir.mkdir(parents=True, exist_ok=True)
    DepPath = OutDir / f"Deps-{Worker}.json"
    _ = DepPath.write_text(JsonLib.dumps(Payload, indent=1) + "\n", encoding="utf-8")
