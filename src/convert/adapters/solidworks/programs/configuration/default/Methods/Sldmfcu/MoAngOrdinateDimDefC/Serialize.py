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
            (8457, 4, 169, "primitive:int", 1),
            (8461, 4, 185, "primitive:int", 21),
            (8465, 4, 201, "primitive:int", 0),
            (8469, 4, 217, "primitive:int", 0),
            (8473, 4, 233, "primitive:int", 0),
        ),
    },
)
