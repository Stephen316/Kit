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
            (838, 2, 112, "primitive:ushort", 0),
            (904, 2, 112, "primitive:ushort", 3),
            (4233, 2, 112, "primitive:ushort", 0),
            (4299, 2, 112, "primitive:ushort", 3),
            (4743, 2, 112, "primitive:ushort", 2),
            (5179, 2, 112, "primitive:ushort", 0),
            (5245, 2, 112, "primitive:ushort", 3),
            (5677, 2, 112, "primitive:ushort", 0),
            (5743, 2, 112, "primitive:ushort", 3),
            (6183, 2, 112, "primitive:ushort", 0),
            (6249, 2, 112, "primitive:ushort", 3),
            (6685, 2, 112, "primitive:ushort", 0),
            (6751, 2, 112, "primitive:ushort", 3),
            (7199, 2, 112, "primitive:ushort", 0),
            (7265, 2, 112, "primitive:ushort", 3),
            (7737, 2, 112, "primitive:ushort", 0),
            (7803, 2, 112, "primitive:ushort", 3),
            (8243, 2, 112, "primitive:ushort", 2),
            (8695, 2, 112, "primitive:ushort", 0),
            (8761, 2, 112, "primitive:ushort", 3),
        ),
    },
)
