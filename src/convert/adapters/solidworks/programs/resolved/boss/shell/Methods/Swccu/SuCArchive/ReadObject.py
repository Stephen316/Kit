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
            (8716, 4, 370, "primitive:long", 4),
            (8736, 4, 370, "primitive:long", 3),
            (8756, 4, 370, "primitive:long", 2),
            (8776, 4, 370, "primitive:long", 1),
            (8882, 4, 370, "primitive:long", 4),
            (8902, 4, 370, "primitive:long", 1),
            (8922, 4, 370, "primitive:long", 2),
            (8942, 4, 370, "primitive:long", 3),
            (9082, 4, 370, "primitive:long", 5),
            (11428, 4, 370, "primitive:long", 8),
            (11682, 4, 370, "primitive:long", 4),
            (11702, 4, 370, "primitive:long", 1),
            (11722, 4, 370, "primitive:long", 2),
            (11742, 4, 370, "primitive:long", 3),
            (13716, 4, 370, "primitive:long", 4),
            (13760, 4, 370, "primitive:long", 3),
            (13780, 4, 370, "primitive:long", 1),
        ),
    },
)
