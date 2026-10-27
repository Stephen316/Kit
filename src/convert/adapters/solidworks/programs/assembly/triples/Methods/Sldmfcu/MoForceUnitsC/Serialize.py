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
            (2523, 2, 72, "primitive:ushort", 0),
            (2974, 2, 72, "primitive:ushort", 4),
            (3058, 2, 72, "primitive:ushort", 2),
            (5539, 2, 72, "primitive:ushort", 0),
            (5983, 2, 72, "primitive:ushort", 0),
            (6485, 2, 72, "primitive:ushort", 0),
            (6983, 2, 72, "primitive:ushort", 0),
            (7489, 2, 72, "primitive:ushort", 0),
            (7991, 2, 72, "primitive:ushort", 0),
            (8505, 2, 72, "primitive:ushort", 0),
            (9043, 2, 72, "primitive:ushort", 0),
            (9483, 2, 72, "primitive:ushort", 0),
            (10001, 2, 72, "primitive:ushort", 0),
        ),
    },
)
