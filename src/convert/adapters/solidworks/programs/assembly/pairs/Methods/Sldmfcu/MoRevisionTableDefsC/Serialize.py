# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoRevisionTableDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (11681, 4, 146, "primitive:int", 0),
            (11685, 4, 159, "primitive:int", 0),
            (11689, 4, 172, "primitive:int", 1),
            (11693, 4, 185, "primitive:int", 0),
            (11697, 4, 215, "primitive:int", 0),
        ),
    },
)
