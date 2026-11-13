from __future__ import annotations

import json as JsonLib
from collections.abc import Mapping
from pathlib import Path as FilePath


def WriteCarried(
    CarriedPath: FilePath | None, Entries: Mapping[str, Mapping[str, object]]
) -> None:
    if CarriedPath is None:
        return
    CarriedPath.parent.mkdir(parents=True, exist_ok=True)
    Payload = JsonLib.dumps({"Modules": dict(sorted(Entries.items()))}, indent=1)
    _ = CarriedPath.write_text(Payload + "\n", encoding="utf-8")
