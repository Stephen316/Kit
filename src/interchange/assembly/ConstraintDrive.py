# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.AssemblyEnums import MateAlignment
from interchange.records.RecordParameter import ParameterValue


# solvers evaluate bindings and orientation intent so those reads share one view
class ConstraintDrive:
    __slots__ = ()

    # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "value"))

    # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "parameter_ids"))

    # alignment choice keeps orientation intent explicit for export writers
    @property
    def Alignment(self) -> MateAlignment | str:
        return CastValue(MateAlignment | str, getattr(self, "alignment"))

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return CastValue(bool, getattr(self, "suppressed"))

    # driving flag splits real constraints from reference measurements
    @property
    def IsDriving(self) -> bool:
        return CastValue(bool, getattr(self, "driving"))
