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
            (10686, 4, 290, "primitive:ulong", 8),
            (10690, 4, 350, "primitive:ulong", 16),
            (10694, 4, 363, "primitive:ulong", 1),
            (10698, 4, 376, "primitive:ulong", 1),
            (15888, 4, 290, "primitive:ulong", 8),
            (15892, 4, 350, "primitive:ulong", 16),
            (15896, 4, 363, "primitive:ulong", 1),
            (15900, 4, 376, "primitive:ulong", 1),
        ),
    },
)
