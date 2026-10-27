# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldarchiveu.Functions.MoGetModelnameFromPath import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9514, 1, 3156, "primitive:uchar", 0),
            (9519, 4, 3701, "primitive:long", 0),
            (9523, 4, 3762, "primitive:long", 0),
            (9527, 4, 3826, "primitive:long", 0),
            (9549, 4, 3839, "primitive:long", 0),
            (9553, 4, 3934, "primitive:long", 0),
            (9561, 4, 4388, "primitive:long", 0),
        ),
    },
)
