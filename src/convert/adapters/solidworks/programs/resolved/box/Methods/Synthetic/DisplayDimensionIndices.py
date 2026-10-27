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
            (8912, 2, "DisplayDimensionOneIndex", "direct:H", 0),
            (10401, 2, "DisplayDimensionTwoIndex", "direct:H", 0),
            (13451, 2, "DisplayDimensionThreeIndex", "direct:H", 0),
        ),
    },
)
