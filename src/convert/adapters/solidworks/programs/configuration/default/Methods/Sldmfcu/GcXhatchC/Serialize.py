# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.GcXhatchC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2672, 8, 812, "primitive:double", float.fromhex("0x0.0p+0")),
            (2680, 8, 825, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2688, 4, 927, "primitive:int", 0),
            (2692, 4, 968, "primitive:int", 0),
            (2696, 4, 997, "primitive:int", 1),
            (2700, 4, 1026, "primitive:int", -1),
            (2704, 4, 1039, "primitive:int", -1),
            (2708, 4, 1098, "primitive:int", 0),
        ),
    },
)
