# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass


# stored sibling order and placement belong to the occurrence rather than its definition
@Dataclass(frozen=True, slots=True)
class NativeOccur:
    ObjectId: int
    ComponentId: int
    OwnerId: int
    Name: str
    InstanceNumber: int
    NativeGuid: str
    Order: int
    Transform: tuple[float, ...]
