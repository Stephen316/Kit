# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters import AdapterRegistry
from convert.engine import ConversionEngine


# one discovery factory keeps the public composition root independent from format packages
def BuildRegistry() -> AdapterRegistry:
    RegistryData = AdapterRegistry()
    _ = RegistryData.introspect()
    return RegistryData


# one shared registry keeps public discovery and conversion selections consistent
KAdapterRegistry = BuildRegistry()

# one shared engine keeps public operations on the same introspected adapter set
KConvertEngine = ConversionEngine(KAdapterRegistry)


# compatibility callers need access to the already introspected shared registry
def GetRegistry() -> AdapterRegistry:
    return KAdapterRegistry
