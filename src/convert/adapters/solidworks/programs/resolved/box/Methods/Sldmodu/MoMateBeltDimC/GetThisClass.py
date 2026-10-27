# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMateBeltDimC.GetThisClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9385, 4, 290, "primitive:ulong", 8),
            (9389, 4, 350, "primitive:ulong", 16),
            (9393, 4, 363, "primitive:ulong", 1),
            (9397, 4, 376, "primitive:ulong", 1),
            (10850, 4, 290, "primitive:ulong", 8),
            (10854, 4, 350, "primitive:ulong", 16),
            (10858, 4, 363, "primitive:ulong", 1),
            (10862, 4, 376, "primitive:ulong", 1),
            (14252, 4, 290, "primitive:ulong", 8),
            (14256, 4, 350, "primitive:ulong", 16),
            (14260, 4, 363, "primitive:ulong", 1),
            (14264, 4, 376, "primitive:ulong", 1),
        ),
    },
)
