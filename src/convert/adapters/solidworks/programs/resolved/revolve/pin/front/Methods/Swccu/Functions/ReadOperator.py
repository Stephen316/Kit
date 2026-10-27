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
            (767, 4, 19, "primitive:ulong", 1785928015),
            (886, 4, 19, "primitive:ulong", 1785928015),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6564, 4, 19, "primitive:ulong", 1763334902),
            (9125, 4, 19, "primitive:ulong", 1763334902),
            (9627, 4, 19, "primitive:ulong", 1785928014),
            (9645, 4, 19, "primitive:ulong", 0),
            (9687, 4, 19, "primitive:ulong", 0),
            (9699, 4, 19, "primitive:ulong", 1785928015),
            (9719, 4, 19, "primitive:ulong", 1785928015),
            (9741, 4, 19, "primitive:ulong", 1785928015),
            (9823, 4, 19, "primitive:ulong", 1785928015),
            (9843, 4, 19, "primitive:ulong", 1785928015),
            (9865, 4, 19, "primitive:ulong", 1785928015),
            (10200, 4, 19, "primitive:ulong", 1785928015),
        ),
    },
)
