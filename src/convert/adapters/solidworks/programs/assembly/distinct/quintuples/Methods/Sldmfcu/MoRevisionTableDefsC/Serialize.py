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
            (13003, 4, 146, "primitive:int", 0),
            (13007, 4, 159, "primitive:int", 0),
            (13011, 4, 172, "primitive:int", 1),
            (13015, 4, 185, "primitive:int", 0),
            (13019, 4, 215, "primitive:int", 0),
        ),
    },
)
