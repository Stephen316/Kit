# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.Functions.ReadOperator import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (767, 4, 19, "primitive:ulong", 1785797027),
            (886, 4, 19, "primitive:ulong", 1785797028),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6564, 4, 19, "primitive:ulong", 1763334902),
            (8995, 4, 19, "primitive:ulong", 1763334902),
            (9497, 4, 19, "primitive:ulong", 1785797026),
            (9515, 4, 19, "primitive:ulong", 0),
            (9557, 4, 19, "primitive:ulong", 0),
            (9569, 4, 19, "primitive:ulong", 1785797028),
            (9589, 4, 19, "primitive:ulong", 1785797028),
            (9611, 4, 19, "primitive:ulong", 1785797028),
            (9693, 4, 19, "primitive:ulong", 1785797028),
            (9713, 4, 19, "primitive:ulong", 1785797028),
            (9735, 4, 19, "primitive:ulong", 1785797028),
            (10070, 4, 19, "primitive:ulong", 1785797027),
        ),
    },
)
