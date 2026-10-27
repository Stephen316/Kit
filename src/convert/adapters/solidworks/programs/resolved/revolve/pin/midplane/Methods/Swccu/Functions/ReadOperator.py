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
            (767, 4, 19, "primitive:ulong", 1786487441),
            (886, 4, 19, "primitive:ulong", 1786487442),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6564, 4, 19, "primitive:ulong", 1763334902),
            (9125, 4, 19, "primitive:ulong", 1763334902),
            (9699, 4, 19, "primitive:ulong", 1786487434),
            (9717, 4, 19, "primitive:ulong", 0),
            (9759, 4, 19, "primitive:ulong", 0),
            (9771, 4, 19, "primitive:ulong", 1786487442),
            (9791, 4, 19, "primitive:ulong", 1786487442),
            (9813, 4, 19, "primitive:ulong", 1786487442),
            (9895, 4, 19, "primitive:ulong", 1786487442),
            (9915, 4, 19, "primitive:ulong", 1786487442),
            (9937, 4, 19, "primitive:ulong", 1786487442),
            (10272, 4, 19, "primitive:ulong", 1786487441),
        ),
    },
)
