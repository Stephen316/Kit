# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping


# enforced write values prevent callers from weakening portable self contained output guarantees
def BuildWriteVals(
    InputValues: TypeMap[str, object] | None,
    AllowCarrier: bool,
) -> TypeMap[str, object]:
    SelectedValues: dict[str, object] = {"portable": True}
    if InputValues is not None:
        SelectedValues.update(InputValues)
    SelectedValues["allow_carrier"] = AllowCarrier
    SelectedValues["require_self_contained"] = True
    return FreezeMapping(SelectedValues)
