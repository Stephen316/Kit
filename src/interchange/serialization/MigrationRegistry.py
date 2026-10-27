# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Callable as CallableType
from typing import Mapping as TypeMap

from interchange.serialization.Wire import GetWireType

# migrations preserve old documents when record schemas evolve compatibly
KMigrationRegistry: dict[
    type[object], CallableType[[TypeMap[str, object]], TypeMap[str, object]]
] = {}


# schema migrations belong beside registration so decoding applies them consistently
def RegMigration(
    TargetType: type[object],
    MigrationFunc: CallableType[[TypeMap[str, object]], TypeMap[str, object]],
) -> None:
    ExistingFunc = KMigrationRegistry.get(TargetType)
    if ExistingFunc is not None and ExistingFunc is not MigrationFunc:
        raise ValueError(
            f"duplicate interchange migration for {GetWireType(TargetType)!r}"
        )
    KMigrationRegistry[TargetType] = MigrationFunc
