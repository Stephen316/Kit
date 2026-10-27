# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionIndices import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10338, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (15617, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (20687, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
            (25761, 2, "DisplayDimensionFourIndex", "direct:H", 0),
        ),
    },
)
