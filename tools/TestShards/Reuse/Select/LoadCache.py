from __future__ import annotations

import json as JsonLib
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.CacheVersion import KCacheVersion
from tools.TestShards.Reuse.Cache.ReadObject import ReadObject
from tools.TestShards.Reuse.Select.CacheData import CacheData


def LoadCache(CachePath: FilePath) -> CacheData:
    Decoded: object = JsonLib.loads(CachePath.read_text(encoding="utf-8"))
    Fields = ReadObject(Decoded, CachePath.name)
    if Fields.get("Version") != KCacheVersion:
        raise ValueError("the test cache has an unsupported version")
    RunText = Fields.get("Run")
    if not isinstance(RunText, str):
        raise ValueError("the test cache does not name its run")
    Modules = ReadObject(Fields.get("Modules"), "Modules")
    return CacheData(
        RunText,
        ReadObject(Fields.get("Guard"), "Guard"),
        {ModKey: ReadObject(Entry, ModKey) for ModKey, Entry in Modules.items()},
    )
