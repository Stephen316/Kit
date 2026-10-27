# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionDirectSlots import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9846, 4, "DisplayDimensionOneDirectSlot", "direct:I", 0),
            (14280, 4, "DisplayDimensionThreeDirectSlot", "direct:I", 0),
            (17518, 4, "DisplayDimensionFiveDirectSlot", "direct:I", 0),
            (19609, 4, "DisplayDimensionSixDirectSlot", "direct:I", 0),
            (21192, 4, "DisplayDimensionSevenDirectSlot", "direct:I", 0),
        ),
    },
)
