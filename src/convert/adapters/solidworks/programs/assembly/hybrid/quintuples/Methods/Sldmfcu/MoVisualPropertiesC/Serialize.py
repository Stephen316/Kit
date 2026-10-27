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
            (2706, 4, 364, "primitive:ulong", 12632256),
            (2710, 4, 393, "primitive:ulong", 0),
            (2714, 4, 425, "primitive:ulong", 12632256),
            (2826, 4, 529, "primitive:int", 0),
            (2830, 4, 558, "primitive:int", 1),
            (2838, 4, 616, "primitive:int", 0),
            (2842, 4, 683, "primitive:int", 0),
            (2846, 4, 712, "primitive:int", -1),
            (2850, 4, 741, "primitive:int", 0),
            (2854, 4, 773, "primitive:int", 0),
            (2858, 4, 810, "primitive:int", 0),
        ),
    },
)
