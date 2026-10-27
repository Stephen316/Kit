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
        "Contents/Config-0": (
            (11293, 4, 133, "primitive:int", 0),
            (11297, 4, 153, "primitive:int", 1),
            (11301, 4, 166, "primitive:int", 0),
            (11305, 4, 179, "primitive:int", 1),
            (11309, 4, 192, "primitive:int", 0),
            (11313, 4, 206, "primitive:int", 0),
        ),
    },
)
