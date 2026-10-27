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
            (9727, 4, 370, "primitive:long", 6),
            (9747, 4, 370, "primitive:long", 5),
            (9767, 4, 370, "primitive:long", 4),
            (9787, 4, 370, "primitive:long", 3),
            (9807, 4, 370, "primitive:long", 2),
            (9827, 4, 370, "primitive:long", 1),
            (9933, 4, 370, "primitive:long", 6),
            (9953, 4, 370, "primitive:long", 1),
            (9973, 4, 370, "primitive:long", 2),
            (9993, 4, 370, "primitive:long", 3),
            (10013, 4, 370, "primitive:long", 4),
            (10033, 4, 370, "primitive:long", 5),
            (10173, 4, 370, "primitive:long", 5),
        ),
    },
)
