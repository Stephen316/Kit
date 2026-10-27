# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5739, 4, 4724, "primitive:ulong", 0),
            (5743, 4, 4744, "primitive:long", 0),
            (5747, 4, 1931, "primitive:long", 3),
            (5752, 4, 2342, "primitive:long", 0),
            (5762, 4, 3319, "primitive:ulong", 100000),
            (8432, 4, 4724, "primitive:ulong", 1),
            (8436, 4, 4744, "primitive:long", 1),
            (8539, 4, 1931, "primitive:long", 3),
            (8544, 4, 2342, "primitive:long", 0),
            (8554, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
