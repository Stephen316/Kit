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
            (5858, 4, 4724, "primitive:ulong", 0),
            (5862, 4, 4744, "primitive:long", 0),
            (5866, 4, 1931, "primitive:long", 3),
            (5871, 4, 2342, "primitive:long", 0),
            (5881, 4, 3319, "primitive:ulong", 100000),
            (7979, 4, 4724, "primitive:ulong", 1),
            (7983, 4, 4744, "primitive:long", 1),
            (8086, 4, 1931, "primitive:long", 3),
            (8091, 4, 2342, "primitive:long", 0),
            (8101, 4, 3319, "primitive:ulong", 100000),
            (14284, 4, 4724, "primitive:ulong", 1),
            (14288, 4, 4744, "primitive:long", 1),
            (14372, 4, 1931, "primitive:long", 3),
            (14377, 4, 2342, "primitive:long", 0),
            (14387, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
