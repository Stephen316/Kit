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
            (767, 4, 19, "primitive:ulong", 1785841757),
            (886, 4, 19, "primitive:ulong", 1785841757),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6584, 4, 19, "primitive:ulong", 1763334902),
            (9092, 4, 19, "primitive:ulong", 1763334902),
            (9600, 4, 19, "primitive:ulong", 1785841750),
            (9618, 4, 19, "primitive:ulong", 0),
            (9660, 4, 19, "primitive:ulong", 0),
            (9672, 4, 19, "primitive:ulong", 1785841757),
            (9723, 4, 19, "primitive:ulong", 1785841757),
            (9743, 4, 19, "primitive:ulong", 1785841757),
            (9763, 4, 19, "primitive:ulong", 1785841757),
            (9783, 4, 19, "primitive:ulong", 1785841757),
            (9803, 4, 19, "primitive:ulong", 1785841757),
            (9823, 4, 19, "primitive:ulong", 1785841757),
            (9905, 4, 19, "primitive:ulong", 1785841757),
            (9929, 4, 19, "primitive:ulong", 1785841757),
            (9949, 4, 19, "primitive:ulong", 1785841757),
            (9969, 4, 19, "primitive:ulong", 1785841757),
            (9989, 4, 19, "primitive:ulong", 1785841757),
            (10009, 4, 19, "primitive:ulong", 1785841757),
            (10029, 4, 19, "primitive:ulong", 1785841757),
        ),
    },
)
