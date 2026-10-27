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
            (10738, 4, 1928, "primitive:long", 0),
            (10742, 4, 1948, "primitive:long", -1),
            (10746, 4, 2000, "primitive:ulong", 0),
            (15920, 4, 1928, "primitive:long", 0),
            (15924, 4, 1948, "primitive:long", -1),
            (15928, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
