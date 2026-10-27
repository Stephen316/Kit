# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoWeldFavoriteC.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (10976, 4, 1928, "primitive:long", 0),
            (10980, 4, 1948, "primitive:long", -1),
            (10984, 4, 2000, "primitive:ulong", 0),
            (16144, 4, 1928, "primitive:long", 0),
            (16148, 4, 1948, "primitive:long", -1),
            (16152, 4, 2000, "primitive:ulong", 0),
            (20467, 4, 1928, "primitive:long", 0),
            (20471, 4, 1948, "primitive:long", -1),
            (20475, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
