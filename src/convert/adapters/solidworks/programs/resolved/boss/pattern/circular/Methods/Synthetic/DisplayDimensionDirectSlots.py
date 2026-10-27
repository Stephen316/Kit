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
            (10311, 4, "DisplayDimensionOneDirectSlot", "direct:I", 0),
            (16275, 4, "DisplayDimensionFourDirectSlot", "direct:I", 0),
            (18401, 4, "DisplayDimensionFiveDirectSlot", "direct:I", 0),
        ),
    },
)
