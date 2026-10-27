# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ReadOptions import ReadOptions
from convert.api.ApiContext import KConvertEngine


# public reads centralize option construction so adapters receive one stable contract
def OpenDocument(
    SourceData: Source,
    *,
    SourceFormat: str | None = None,
    Configuration: str | None = None,
    IncludeBrep: bool = True,
    IncludeTess: bool = True,
    StrictMode: bool = True,
) -> CadDocument:
    return KConvertEngine.read(
        SourceData,
        format_id=SourceFormat,
        options=ReadOptions(
            configuration=Configuration,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTess,
            strict=StrictMode,
        ),
    )
