# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# wire bindings remain distinct from their projected values and profile geometry
@Dataclass(frozen=True, slots=True)
class NativeExtrude:
    AlongId: int
    AgainstId: int | None
    StartId: int | None
    TaperId: int | None
    SecondTaperId: int | None
    SideMode: str
    Direction: tuple[float, float, float]
    ProfileId: int
    ProxyId: int
