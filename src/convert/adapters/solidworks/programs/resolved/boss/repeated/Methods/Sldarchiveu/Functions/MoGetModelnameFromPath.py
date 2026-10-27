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
            (8725, 1, 3156, "primitive:uchar", 0),
            (8730, 4, 3701, "primitive:long", 0),
            (8734, 4, 3762, "primitive:long", 0),
            (8738, 4, 3826, "primitive:long", 0),
            (8760, 4, 3839, "primitive:long", 0),
            (8764, 4, 3934, "primitive:long", 0),
            (8772, 4, 4388, "primitive:long", 0),
        ),
    },
)
