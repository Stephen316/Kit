# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.api.ApiContext import KAdapterRegistry


# public discovery merges read and write formats so callers see one deterministic catalog
def ListAdapters() -> tuple[AdapterInfo, ...]:
    AdapterMap = {
        AdapterData.info.format_id: AdapterData.info
        for AdapterData in KAdapterRegistry.readers()
    }
    AdapterMap.update(
        {
            AdapterData.info.format_id: AdapterData.info
            for AdapterData in KAdapterRegistry.writers()
        }
    )
    return tuple(AdapterMap[FormatId] for FormatId in sorted(AdapterMap))
