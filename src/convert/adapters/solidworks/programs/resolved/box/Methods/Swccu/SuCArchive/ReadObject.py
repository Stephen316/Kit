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
            (12450, 4, 370, "primitive:long", 4),
            (12470, 4, 370, "primitive:long", 3),
            (12490, 4, 370, "primitive:long", 2),
            (12510, 4, 370, "primitive:long", 1),
            (12616, 4, 370, "primitive:long", 4),
            (12636, 4, 370, "primitive:long", 1),
            (12656, 4, 370, "primitive:long", 2),
            (12676, 4, 370, "primitive:long", 3),
            (12816, 4, 370, "primitive:long", 5),
        ),
    },
)
