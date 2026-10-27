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
        "Configuration": (
            (11225, 4, 146, "primitive:int", 0),
            (11229, 4, 159, "primitive:int", 0),
            (11233, 4, 172, "primitive:int", 1),
            (11237, 4, 185, "primitive:int", 0),
            (11241, 4, 215, "primitive:int", 0),
        ),
    },
)
