# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAngOrdinateDimDefC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (8487, 4, 169, "primitive:int", 1),
            (8491, 4, 185, "primitive:int", 21),
            (8495, 4, 201, "primitive:int", 0),
            (8499, 4, 217, "primitive:int", 0),
            (8503, 4, 233, "primitive:int", 0),
        ),
    },
)
