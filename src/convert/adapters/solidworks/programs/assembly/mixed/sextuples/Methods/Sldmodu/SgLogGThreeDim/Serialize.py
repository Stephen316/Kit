# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGThreeDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4892, 2, 13751, "primitive:ushort", 31),
            (4910, 2, 13906, "primitive:ushort", 1),
            (4912, 2, 13996, "primitive:ushort", 0),
            (4918, 2, 14480, "primitive:ushort", 0),
            (4920, 4, 14546, "primitive:long", -2),
            (4956, 2, 14739, "primitive:ushort", 0),
            (4958, 2, 14916, "primitive:ushort", 0),
            (5296, 4, 2988, "primitive:long", 0),
        ),
    },
)
