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
            (10201, 4, 133, "primitive:int", 0),
            (10205, 4, 153, "primitive:int", 1),
            (10209, 4, 166, "primitive:int", 0),
            (10213, 4, 179, "primitive:int", 1),
            (10217, 4, 192, "primitive:int", 0),
            (10221, 4, 206, "primitive:int", 0),
        ),
    },
)
