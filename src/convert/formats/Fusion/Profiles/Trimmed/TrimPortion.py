# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# native selector identity remains separate from derived increasing geometric parameters
@Dataclass(frozen=True, slots=True)
class TrimPortion:
    EntityId: str
    Lower: float
    Upper: float
    Selector: tuple[int, ...]
