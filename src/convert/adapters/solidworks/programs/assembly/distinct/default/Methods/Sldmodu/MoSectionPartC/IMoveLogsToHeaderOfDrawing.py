# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSectionPartC.IMoveLogsToHeaderOfDrawing import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (2446, 4, 9888, "primitive:long", 0),
            (2450, 4, 9904, "primitive:long", 0),
            (2454, 4, 9922, "primitive:long", 0),
        ),
    },
)
