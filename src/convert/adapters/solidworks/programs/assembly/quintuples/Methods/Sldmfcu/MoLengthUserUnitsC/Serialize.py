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
        "Contents/Config-0": (
            (3431, 2, 112, "primitive:ushort", 0),
            (3497, 2, 112, "primitive:ushort", 3),
            (6471, 2, 112, "primitive:ushort", 0),
            (6537, 2, 112, "primitive:ushort", 3),
            (6981, 2, 112, "primitive:ushort", 2),
            (7417, 2, 112, "primitive:ushort", 0),
            (7483, 2, 112, "primitive:ushort", 3),
            (7915, 2, 112, "primitive:ushort", 0),
            (7981, 2, 112, "primitive:ushort", 3),
            (8421, 2, 112, "primitive:ushort", 0),
            (8487, 2, 112, "primitive:ushort", 3),
            (8923, 2, 112, "primitive:ushort", 0),
            (8989, 2, 112, "primitive:ushort", 3),
            (9437, 2, 112, "primitive:ushort", 0),
            (9503, 2, 112, "primitive:ushort", 3),
            (9975, 2, 112, "primitive:ushort", 0),
            (10041, 2, 112, "primitive:ushort", 3),
            (10481, 2, 112, "primitive:ushort", 2),
            (10933, 2, 112, "primitive:ushort", 0),
            (10999, 2, 112, "primitive:ushort", 3),
        ),
    },
)
