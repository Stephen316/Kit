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
            (10450, 4, 290, "primitive:ulong", 8),
            (10454, 4, 350, "primitive:ulong", 16),
            (10458, 4, 363, "primitive:ulong", 1),
            (10462, 4, 376, "primitive:ulong", 1),
        ),
    },
)
