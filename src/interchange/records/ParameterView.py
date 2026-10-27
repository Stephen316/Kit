# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from typing import cast as CastValue

from interchange.enums.EnumValues import ParameterRole

if IsTypeCheck:
    from interchange.records.RecordParameter import (
        Expression,  # lgtm[py/unsafe-cyclic-import]
        ParameterValue,  # lgtm[py/unsafe-cyclic-import]
    )


# parameter consumers read values roles and formulas through one typed view
class ParameterView:
    __slots__: tuple[str, ...] = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> ParameterValue:
        return CastValue("ParameterValue", getattr(self, "value"))

    # role tags separate driven driving and reference usages cleanly
    @property
    def ValueRole(self) -> ParameterRole:
        return CastValue(ParameterRole, getattr(self, "role"))

    # optional formula keeps derived values live instead of frozen snapshots
    @property
    def Expression(self) -> Expression | None:
        return CastValue("Expression | None", getattr(self, "expression"))

    # owner link ties parameters to features without back references
    @property
    def OwnerId(self) -> str:
        return CastValue(str, getattr(self, "owner_id"))
