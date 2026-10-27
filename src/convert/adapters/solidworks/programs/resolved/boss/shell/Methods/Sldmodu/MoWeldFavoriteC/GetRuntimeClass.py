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
            (10619, 4, 1928, "primitive:long", 0),
            (10623, 4, 1948, "primitive:long", -1),
            (10627, 4, 2000, "primitive:ulong", 0),
            (13096, 4, 1928, "primitive:long", 0),
            (13100, 4, 1948, "primitive:long", -1),
            (13104, 4, 2000, "primitive:ulong", 0),
        ),
    },
)
