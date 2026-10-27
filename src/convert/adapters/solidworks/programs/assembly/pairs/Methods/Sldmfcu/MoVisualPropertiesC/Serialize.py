# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoVisualPropertiesC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1384, 4, 364, "primitive:ulong", 12632256),
            (1388, 4, 393, "primitive:ulong", 0),
            (1392, 4, 425, "primitive:ulong", 12632256),
            (1504, 4, 529, "primitive:int", 0),
            (1508, 4, 558, "primitive:int", 1),
            (1516, 4, 616, "primitive:int", 0),
            (1520, 4, 683, "primitive:int", 0),
            (1524, 4, 712, "primitive:int", -1),
            (1528, 4, 741, "primitive:int", 0),
            (1532, 4, 773, "primitive:int", 0),
            (1536, 4, 810, "primitive:int", 0),
        ),
    },
)
