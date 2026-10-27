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
            (1211, 2, 72, "primitive:ushort", 0),
            (1662, 2, 72, "primitive:ushort", 4),
            (1746, 2, 72, "primitive:ushort", 2),
            (4227, 2, 72, "primitive:ushort", 0),
            (4671, 2, 72, "primitive:ushort", 0),
            (5173, 2, 72, "primitive:ushort", 0),
            (5671, 2, 72, "primitive:ushort", 0),
            (6177, 2, 72, "primitive:ushort", 0),
            (6679, 2, 72, "primitive:ushort", 0),
            (7193, 2, 72, "primitive:ushort", 0),
            (7731, 2, 72, "primitive:ushort", 0),
            (8171, 2, 72, "primitive:ushort", 0),
            (8689, 2, 72, "primitive:ushort", 0),
        ),
    },
)
