# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert import available_adapters as AvailableAdapters
from interchange import CadDocument
from interchange import CadSource


# needed because smoke tests must prove packages import before expensive suites
def TestPkgImports() -> None:
    assert (
        CadDocument(
            source=CadSource(format_id="smoke", path="", sha256=""),
            configurations=(),
            parameters=(),
            support_planes=(),
            sketches=(),
            selections=(),
            feature_timeline=(),
            bodies=(),
        ).schema_version
        == "1.0"
    )


# needed because smoke tests must prove adapter discovery remains publicly available
def TestRegistry() -> None:
    AdapterNames = {AdapterInfo.name for AdapterInfo in AvailableAdapters()}
    assert "Kit interchange JSON" in AdapterNames
