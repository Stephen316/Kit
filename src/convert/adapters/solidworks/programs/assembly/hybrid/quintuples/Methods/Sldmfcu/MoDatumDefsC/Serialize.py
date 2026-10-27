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
            (11431, 4, 133, "primitive:int", 0),
            (11435, 4, 153, "primitive:int", 1),
            (11439, 4, 166, "primitive:int", 0),
            (11443, 4, 179, "primitive:int", 1),
            (11447, 4, 192, "primitive:int", 0),
            (11451, 4, 206, "primitive:int", 0),
        ),
    },
)
