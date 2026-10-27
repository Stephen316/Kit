# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLengthUserUnitsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (840, 2, 112, "primitive:ushort", 0),
            (906, 2, 112, "primitive:ushort", 3),
            (4203, 2, 112, "primitive:ushort", 0),
            (4269, 2, 112, "primitive:ushort", 3),
            (4713, 2, 112, "primitive:ushort", 2),
            (5149, 2, 112, "primitive:ushort", 0),
            (5215, 2, 112, "primitive:ushort", 3),
            (5647, 2, 112, "primitive:ushort", 0),
            (5713, 2, 112, "primitive:ushort", 3),
            (6153, 2, 112, "primitive:ushort", 0),
            (6219, 2, 112, "primitive:ushort", 3),
            (6655, 2, 112, "primitive:ushort", 0),
            (6721, 2, 112, "primitive:ushort", 3),
            (7169, 2, 112, "primitive:ushort", 0),
            (7235, 2, 112, "primitive:ushort", 3),
            (7707, 2, 112, "primitive:ushort", 0),
            (7773, 2, 112, "primitive:ushort", 3),
            (8213, 2, 112, "primitive:ushort", 2),
            (8665, 2, 112, "primitive:ushort", 0),
            (8731, 2, 112, "primitive:ushort", 3),
        ),
    },
)
