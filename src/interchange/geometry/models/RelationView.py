# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from typing import cast as CastValue

if IsTypeCheck:
    from interchange.geometry.models.Sketch import (
        ConstraintRef,  # lgtm[py/unsafe-cyclic-import]
    )


# relation consumers read solver intent and bindings through one typed view
class RelationView:
    __slots__: tuple[str, ...] = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> str:
        return CastValue(str, getattr(self, "kind"))

    # reference list ties each relation to the entities it constrains
    @property
    def References(self) -> "tuple[ConstraintRef, ...]":
        return CastValue("tuple[ConstraintRef, ...]", getattr(self, "references"))

    # optional parameter link makes dimensions editable through records
    @property
    def ParameterId(self) -> str | None:
        return CastValue(str | None, getattr(self, "parameter_id"))

    # driving flag splits real constraints from reference measurements
    @property
    def IsDriving(self) -> bool:
        return CastValue(bool, getattr(self, "driving"))

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return CastValue(bool, getattr(self, "suppressed"))
