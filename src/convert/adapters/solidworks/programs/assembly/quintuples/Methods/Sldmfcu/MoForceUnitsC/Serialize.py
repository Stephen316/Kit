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
            (3587, 2, 72, "primitive:ushort", 0),
            (4038, 2, 72, "primitive:ushort", 4),
            (4122, 2, 72, "primitive:ushort", 2),
            (6603, 2, 72, "primitive:ushort", 0),
            (7047, 2, 72, "primitive:ushort", 0),
            (7549, 2, 72, "primitive:ushort", 0),
            (8047, 2, 72, "primitive:ushort", 0),
            (8553, 2, 72, "primitive:ushort", 0),
            (9055, 2, 72, "primitive:ushort", 0),
            (9569, 2, 72, "primitive:ushort", 0),
            (10107, 2, 72, "primitive:ushort", 0),
            (10547, 2, 72, "primitive:ushort", 0),
            (11065, 2, 72, "primitive:ushort", 0),
        ),
    },
)
