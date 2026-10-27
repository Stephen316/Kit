# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Protocol

from convert.adapters.registry import AdapterRegistry


# engine initialization accepts every coordinator exposing the concrete registry state
class EngineState(Protocol):
    registry: AdapterRegistry


# dependency injection keeps adapter discovery replaceable without cad application coupling
def InitEngineMut(SelfValue: EngineState, RegistryData: AdapterRegistry) -> None:
    SelfValue.registry = RegistryData
