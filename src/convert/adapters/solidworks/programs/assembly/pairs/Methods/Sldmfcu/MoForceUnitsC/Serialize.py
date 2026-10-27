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
            (1805, 2, 72, "primitive:ushort", 0),
            (2256, 2, 72, "primitive:ushort", 4),
            (2340, 2, 72, "primitive:ushort", 2),
            (4821, 2, 72, "primitive:ushort", 0),
            (5265, 2, 72, "primitive:ushort", 0),
            (5767, 2, 72, "primitive:ushort", 0),
            (6265, 2, 72, "primitive:ushort", 0),
            (6771, 2, 72, "primitive:ushort", 0),
            (7273, 2, 72, "primitive:ushort", 0),
            (7787, 2, 72, "primitive:ushort", 0),
            (8325, 2, 72, "primitive:ushort", 0),
            (8765, 2, 72, "primitive:ushort", 0),
            (9283, 2, 72, "primitive:ushort", 0),
        ),
    },
)
