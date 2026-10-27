# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KTargetType as Destination
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry


# write delegation stays isolated because output staging belongs entirely to the registry
class EngineWrite:
    registry: AdapterRegistry

    # direct initialization keeps each engine half usable in isolation
    def __init__(self, Registry: AdapterRegistry) -> None:
        super().__init__()
        self.registry = Registry

    # registry delegation preserves one validation path for every public document write
    def WriteTarget(
        self,
        DocumentData: CadDocument,
        TargetData: Destination,
        *,
        FormatId: str | None = None,
        WriteOpts: WriteOptions | None = None,
    ) -> WriteResult:
        return self.registry.write(
            DocumentData,
            TargetData,
            format_id=FormatId,
            options=WriteOpts or WriteOptions(),
        )
