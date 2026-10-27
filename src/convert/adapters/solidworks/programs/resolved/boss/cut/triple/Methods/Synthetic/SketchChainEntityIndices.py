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
            (8486, 16, "SketchOneFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (8504, 4, "SketchOneSecondChainEntityIndices", "direct:1i", 0),
            (13642, 16, "SketchTwoFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (13660, 4, "SketchTwoSecondChainEntityIndices", "direct:1i", 0),
            (
                18803,
                16,
                "SketchThreeFirstChainEntityIndices",
                "direct:4i",
                (1, 2, 3, 4),
            ),
            (18821, 4, "SketchThreeSecondChainEntityIndices", "direct:1i", 0),
            (23873, 16, "SketchFourFirstChainEntityIndices", "direct:4i", (1, 2, 3, 4)),
            (23891, 4, "SketchFourSecondChainEntityIndices", "direct:1i", 0),
        ),
    },
)
