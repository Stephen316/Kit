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
            (9850, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (12742, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (14284, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
            (16021, 2, "DisplayDimensionFourIndex", "direct:H", 0),
            (17522, 2, "DisplayDimensionFiveIndex", "direct:H", 0),
            (19613, 2, "DisplayDimensionSixIndex", "direct:H", 0),
            (21196, 2, "DisplayDimensionSevenIndex", "direct:H", 0),
        ),
    },
)
