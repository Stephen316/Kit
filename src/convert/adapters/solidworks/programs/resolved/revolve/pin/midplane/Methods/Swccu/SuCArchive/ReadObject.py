# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9775, 4, 370, "primitive:long", 6),
            (9795, 4, 370, "primitive:long", 5),
            (9817, 4, 370, "primitive:long", 7),
            (9899, 4, 370, "primitive:long", 5),
            (9919, 4, 370, "primitive:long", 4),
            (9941, 4, 370, "primitive:long", 6),
            (10077, 4, 370, "primitive:long", 5),
        ),
    },
)
