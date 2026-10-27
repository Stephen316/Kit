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
            (5689, 4, 37887, "primitive:long", 0),
            (5693, 4, 37887, "primitive:long", 0),
            (5697, 4, 37887, "primitive:long", 0),
            (5701, 4, 37887, "primitive:long", 0),
            (7736, 4, 37887, "primitive:long", 0),
            (7740, 4, 37887, "primitive:long", 0),
            (7744, 4, 37887, "primitive:long", 0),
            (7748, 4, 37887, "primitive:long", 0),
        ),
    },
)
