# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# native sidedness and references survive independently of geometric evaluation
@Dataclass(frozen=True, slots=True)
class RevolveInput:
    Operation: str
    ExtentKind: str
    SideMode: str
    IsProjected: bool
    IsSolid: bool
    AlongId: int
    AgainstId: int | None
    AxisId: int
    TargetIds: tuple[int, ...]
