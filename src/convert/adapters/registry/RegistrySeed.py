# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.registry.RegistryBinding import AdapterBinding


# fresh registries start empty because applications need isolated transactional state
class RegistrySeed:
    BindingMap: dict[str, AdapterBinding]
    AliasMap: dict[str, str]

    # empty isolated state supports independent applications tests and transactional discovery
    def __init__(self) -> None:
        super().__init__()
        self.BindingMap = {}
        self.AliasMap = {}
