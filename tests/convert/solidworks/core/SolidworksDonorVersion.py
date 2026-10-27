# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations
import json as JsonLib
from pathlib import Path as FilePath


# keeps this focused behavior isolated so regressions remain immediately visible
def GetDonorVer(FixtureRoot: FilePath, TraceVersion: int | None) -> int | None:
    if TraceVersion is not None:
        return TraceVersion
    Versions = {
        Version
        for MetaPath in FixtureRoot.glob("*/meta.json")
        if isinstance(
            (
                Version := JsonLib.loads(MetaPath.read_text(encoding="utf-8")).get(
                    "mo_version"
                )
            ),
            int,
        )
        and (not isinstance(Version, bool))
    }
    return Versions.pop() if len(Versions) == 1 else None
