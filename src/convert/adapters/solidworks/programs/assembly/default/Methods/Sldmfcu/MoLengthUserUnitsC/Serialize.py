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
            (1055, 2, 112, "primitive:ushort", 0),
            (1121, 2, 112, "primitive:ushort", 3),
            (4095, 2, 112, "primitive:ushort", 0),
            (4161, 2, 112, "primitive:ushort", 3),
            (4605, 2, 112, "primitive:ushort", 2),
            (5041, 2, 112, "primitive:ushort", 0),
            (5107, 2, 112, "primitive:ushort", 3),
            (5539, 2, 112, "primitive:ushort", 0),
            (5605, 2, 112, "primitive:ushort", 3),
            (6045, 2, 112, "primitive:ushort", 0),
            (6111, 2, 112, "primitive:ushort", 3),
            (6547, 2, 112, "primitive:ushort", 0),
            (6613, 2, 112, "primitive:ushort", 3),
            (7061, 2, 112, "primitive:ushort", 0),
            (7127, 2, 112, "primitive:ushort", 3),
            (7599, 2, 112, "primitive:ushort", 0),
            (7665, 2, 112, "primitive:ushort", 3),
            (8105, 2, 112, "primitive:ushort", 2),
            (8557, 2, 112, "primitive:ushort", 0),
            (8623, 2, 112, "primitive:ushort", 3),
        ),
    },
)
