from __future__ import annotations

import json as JsonLib
from pathlib import Path as FilePath

from tools.TestShards.Reuse.Cache.ReadObject import ReadObject


def LoadCarried(CarriedPath: FilePath | None) -> dict[str, dict[str, object]]:
    if CarriedPath is None or not CarriedPath.is_file():
        return {}
    Decoded: object = JsonLib.loads(CarriedPath.read_text(encoding="utf-8"))
    Modules = ReadObject(
        ReadObject(Decoded, CarriedPath.name).get("Modules"), "Modules"
    )
    return {ModKey: ReadObject(Entry, ModKey) for ModKey, Entry in Modules.items()}
