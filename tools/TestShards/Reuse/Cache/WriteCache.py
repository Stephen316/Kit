from __future__ import annotations

import json as JsonLib
from datetime import UTC
from datetime import datetime as DateTime
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.CacheInputs import CacheInputs
from tools.TestShards.Reuse.Cache.CacheVersion import KCacheVersion
from tools.TestShards.Reuse.Cache.ComputeGuard import ComputeGuard
from tools.TestShards.Reuse.Cache.DescribeCache import DescribeCache
from tools.TestShards.Reuse.Cache.MeasureModules import MeasureModules


def WriteCache(Inputs: CacheInputs, RunText: str, OutputPath: FilePath) -> str:
    PythonText = next(iter(Inputs.Graph.Pythons))
    Stamp = {
        "MeasuredAt": DateTime.now(UTC).isoformat(timespec="seconds"),
        "MeasuredRun": RunText,
    }
    Entries, Reasons = MeasureModules(
        Inputs.Graph, Inputs.TreeInfo, Inputs.Outcomes, Stamp
    )
    Carried = {
        ModKey: Entry
        for ModKey, Entry in Inputs.Carried.items()
        if ModKey not in Entries
    }
    Payload = {
        "Version": KCacheVersion,
        "Run": RunText,
        "Guard": ComputeGuard(Inputs.TreeInfo.Blobs, PythonText),
        "Modules": dict(sorted({**Carried, **Entries}.items())),
    }
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    _ = OutputPath.write_text(JsonLib.dumps(Payload, indent=1) + "\n", encoding="utf-8")
    return DescribeCache(len(Entries), len(Carried), Reasons)
