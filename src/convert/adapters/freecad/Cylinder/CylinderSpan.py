# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as Dataclass

from interchange.geometry.models.VectorSpace import SpaceVector


# oriented endpoint evidence retains axial and periodic coordinates separately
@Dataclass(frozen=True, slots=True)
class CylinderSpan:
    StartStation: float
    EndStation: float
    StartRadial: SpaceVector
    EndRadial: SpaceVector
    Sweep: float
