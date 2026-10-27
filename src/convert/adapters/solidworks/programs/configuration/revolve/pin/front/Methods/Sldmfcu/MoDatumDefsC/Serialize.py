# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (9653, 4, 133, "primitive:int", 0),
            (9657, 4, 153, "primitive:int", 1),
            (9661, 4, 166, "primitive:int", 0),
            (9665, 4, 179, "primitive:int", 1),
            (9669, 4, 192, "primitive:int", 0),
            (9673, 4, 206, "primitive:int", 0),
        ),
    },
)
