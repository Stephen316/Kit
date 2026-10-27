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
            (1741, 2, 112, "primitive:ushort", 0),
            (1807, 2, 112, "primitive:ushort", 3),
            (4781, 2, 112, "primitive:ushort", 0),
            (4847, 2, 112, "primitive:ushort", 3),
            (5291, 2, 112, "primitive:ushort", 2),
            (5727, 2, 112, "primitive:ushort", 0),
            (5793, 2, 112, "primitive:ushort", 3),
            (6225, 2, 112, "primitive:ushort", 0),
            (6291, 2, 112, "primitive:ushort", 3),
            (6731, 2, 112, "primitive:ushort", 0),
            (6797, 2, 112, "primitive:ushort", 3),
            (7233, 2, 112, "primitive:ushort", 0),
            (7299, 2, 112, "primitive:ushort", 3),
            (7747, 2, 112, "primitive:ushort", 0),
            (7813, 2, 112, "primitive:ushort", 3),
            (8285, 2, 112, "primitive:ushort", 0),
            (8351, 2, 112, "primitive:ushort", 3),
            (8791, 2, 112, "primitive:ushort", 2),
            (9243, 2, 112, "primitive:ushort", 0),
            (9309, 2, 112, "primitive:ushort", 3),
        ),
    },
)
