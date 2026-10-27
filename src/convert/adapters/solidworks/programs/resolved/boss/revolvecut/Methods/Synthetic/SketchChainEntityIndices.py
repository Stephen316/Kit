# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.SketchChainEntityIndices import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8010, 16, "SketchOneFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (8028, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
            (14296, 16, "SketchTwoFirstChainEntityIndices", "direct:4i", (2, 3, 4, 5)),
            (14314, 4, "SketchTwoSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
