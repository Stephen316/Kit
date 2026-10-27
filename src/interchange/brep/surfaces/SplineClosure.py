# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import cast as CastValue


# rational weights and seam closure shape spline behavior at surface boundaries
class SplineClosure:
    __slots__ = ()

    # rational weights keep conic splines representable exactly rather than approximately
    @property
    def Weights(self) -> tuple[tuple[float, ...], ...]:
        return CastValue(
            tuple[tuple[float, ...], ...],
            getattr(self, "weights"),
        )

    # u periodicity tells evaluators whether seam closure can be assumed
    @property
    def IsPeriodicU(self) -> bool:
        return CastValue(bool, getattr(self, "periodic_u"))

    # v periodicity completes seam handling for closed surfaces
    @property
    def IsPeriodicV(self) -> bool:
        return CastValue(bool, getattr(self, "periodic_v"))
