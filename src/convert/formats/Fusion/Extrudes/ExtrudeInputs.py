# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# raw control fields remain separate from independently verified selection ownership
@Dataclass(frozen=True, slots=True)
class ExtrudeInputs:
    AlongId: int
    AgainstId: int | None
    StartId: int | None
    TaperId: int | None
    SecondTaperId: int | None
    SideMode: str
    Direction: tuple[float, float, float]
    CacheId: int
