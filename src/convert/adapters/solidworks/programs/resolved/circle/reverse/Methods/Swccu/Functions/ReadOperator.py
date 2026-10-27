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
            (767, 4, 19, "primitive:ulong", 1786472138),
            (886, 4, 19, "primitive:ulong", 1786472138),
            (5762, 4, 19, "primitive:ulong", 1763334902),
            (6553, 4, 19, "primitive:ulong", 1763334902),
            (9368, 4, 19, "primitive:ulong", 1763334902),
            (9876, 4, 19, "primitive:ulong", 1786472132),
            (9894, 4, 19, "primitive:ulong", 0),
            (9936, 4, 19, "primitive:ulong", 0),
            (9948, 4, 19, "primitive:ulong", 1786472138),
            (9999, 4, 19, "primitive:ulong", 1786472138),
            (10081, 4, 19, "primitive:ulong", 1786472138),
            (10105, 4, 19, "primitive:ulong", 1786472138),
        ),
    },
)
