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
            (8823, 4, 370, "primitive:long", 4),
            (8843, 4, 370, "primitive:long", 3),
            (8863, 4, 370, "primitive:long", 2),
            (8883, 4, 370, "primitive:long", 1),
            (8989, 4, 370, "primitive:long", 4),
            (9009, 4, 370, "primitive:long", 1),
            (9029, 4, 370, "primitive:long", 2),
            (9049, 4, 370, "primitive:long", 3),
            (9189, 4, 370, "primitive:long", 5),
            (11690, 4, 370, "primitive:long", 4),
            (11734, 4, 370, "primitive:long", 1),
            (11778, 4, 370, "primitive:long", 3),
            (11856, 4, 370, "primitive:long", 8),
            (18775, 4, 370, "primitive:long", 3),
            (18795, 4, 370, "primitive:long", 2),
        ),
    },
)
