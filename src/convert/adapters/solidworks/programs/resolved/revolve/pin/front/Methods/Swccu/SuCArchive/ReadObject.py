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
            (9703, 4, 370, "primitive:long", 6),
            (9723, 4, 370, "primitive:long", 5),
            (9745, 4, 370, "primitive:long", 7),
            (9827, 4, 370, "primitive:long", 5),
            (9847, 4, 370, "primitive:long", 4),
            (9869, 4, 370, "primitive:long", 6),
            (10005, 4, 370, "primitive:long", 5),
        ),
    },
)
