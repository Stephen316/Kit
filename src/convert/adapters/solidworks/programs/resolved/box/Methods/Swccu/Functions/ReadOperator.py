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
            (767, 4, 19, "primitive:ulong", 1786460560),
            (886, 4, 19, "primitive:ulong", 1786460562),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6908, 4, 19, "primitive:ulong", 1763334902),
            (11815, 4, 19, "primitive:ulong", 1763334902),
            (12323, 4, 19, "primitive:ulong", 1786460555),
            (12341, 4, 19, "primitive:ulong", 0),
            (12383, 4, 19, "primitive:ulong", 0),
            (12395, 4, 19, "primitive:ulong", 1786460562),
            (12446, 4, 19, "primitive:ulong", 1786460562),
            (12466, 4, 19, "primitive:ulong", 1786460562),
            (12486, 4, 19, "primitive:ulong", 1786460562),
            (12506, 4, 19, "primitive:ulong", 1786460562),
            (12588, 4, 19, "primitive:ulong", 1786460562),
            (12612, 4, 19, "primitive:ulong", 1786460562),
            (12632, 4, 19, "primitive:ulong", 1786460562),
            (12652, 4, 19, "primitive:ulong", 1786460562),
            (12672, 4, 19, "primitive:ulong", 1786460562),
        ),
    },
)
