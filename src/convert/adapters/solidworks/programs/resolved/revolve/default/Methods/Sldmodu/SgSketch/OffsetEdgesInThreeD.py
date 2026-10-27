# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5570, 4, 37887, "primitive:long", 0),
            (5574, 4, 37887, "primitive:long", 0),
            (5578, 4, 37887, "primitive:long", 0),
            (5582, 4, 37887, "primitive:long", 0),
            (8640, 4, 37887, "primitive:long", 0),
            (8644, 4, 37887, "primitive:long", 0),
            (8648, 4, 37887, "primitive:long", 0),
            (8652, 4, 37887, "primitive:long", 0),
        ),
    },
)
