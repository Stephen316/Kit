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
            (9201, 1, 3156, "primitive:uchar", 0),
            (9206, 4, 3701, "primitive:long", 0),
            (9210, 4, 3762, "primitive:long", 0),
            (9214, 4, 3826, "primitive:long", 0),
            (9236, 4, 3839, "primitive:long", 0),
            (9240, 4, 3934, "primitive:long", 0),
            (9248, 4, 4388, "primitive:long", 0),
        ),
    },
)
