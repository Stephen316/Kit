# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (110, 4, 364, "primitive:ulong", 15651274),
            (114, 4, 393, "primitive:ulong", 0),
            (118, 4, 425, "primitive:ulong", 0),
            (695, 4, 529, "primitive:int", 0),
            (699, 4, 558, "primitive:int", 1),
            (707, 4, 616, "primitive:int", 0),
            (711, 4, 683, "primitive:int", 1),
            (715, 4, 712, "primitive:int", -1),
            (719, 4, 741, "primitive:int", 0),
            (723, 4, 773, "primitive:int", 0),
            (727, 4, 810, "primitive:int", 0),
        ),
    },
)
