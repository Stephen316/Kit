# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoForceUnitsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1897, 2, 72, "primitive:ushort", 0),
            (2348, 2, 72, "primitive:ushort", 4),
            (2432, 2, 72, "primitive:ushort", 2),
            (4913, 2, 72, "primitive:ushort", 0),
            (5357, 2, 72, "primitive:ushort", 0),
            (5859, 2, 72, "primitive:ushort", 0),
            (6357, 2, 72, "primitive:ushort", 0),
            (6863, 2, 72, "primitive:ushort", 0),
            (7365, 2, 72, "primitive:ushort", 0),
            (7879, 2, 72, "primitive:ushort", 0),
            (8417, 2, 72, "primitive:ushort", 0),
            (8857, 2, 72, "primitive:ushort", 0),
            (9375, 2, 72, "primitive:ushort", 0),
        ),
    },
)
