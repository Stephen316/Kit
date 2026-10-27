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
            (10315, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (13213, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (14753, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
            (16279, 2, "DisplayDimensionFourIndex", "direct:H", 0),
            (18405, 2, "DisplayDimensionFiveIndex", "direct:H", 0),
        ),
    },
)
