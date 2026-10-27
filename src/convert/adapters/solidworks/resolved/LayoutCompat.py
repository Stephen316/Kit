# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Protocol as TypeProtocol
from typing import cast as CastValue


# legacy callers retain these feature spellings so one protocol pins their static types
class LayoutCompat(TypeProtocol):

    # compatibility callers retain the original revolution predicate spelling
    @property
    def is_revolution(self) -> bool:
        return CastValue(bool, getattr(self, "IsRevolution"))

    # compatibility callers retain the original angle property spelling
    @property
    def angle_degrees(self) -> float | None:
        return CastValue(float | None, getattr(self, "AngleDegrees"))

    # compatibility callers retain the original corners property spelling
    @property
    def corners_mm(self) -> tuple[tuple[float, float], ...]:
        return CastValue(
            tuple[tuple[float, float], ...],
            getattr(self, "CornersMm"),
        )

    # compatibility callers retain the original radii property spelling
    @property
    def radii_mm(self) -> tuple[float, ...]:
        return CastValue(tuple[float, ...], getattr(self, "RadiiMm"))

    # compatibility callers retain the original bounds property spelling
    @property
    def bounds_mm(self) -> tuple[float, float, float, float] | None:
        return CastValue(
            tuple[float, float, float, float] | None,
            getattr(self, "BoundsMm"),
        )
