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
            (2728, 4, 364, "primitive:ulong", 12632256),
            (2732, 4, 393, "primitive:ulong", 0),
            (2736, 4, 425, "primitive:ulong", 12632256),
            (2848, 4, 529, "primitive:int", 0),
            (2852, 4, 558, "primitive:int", 1),
            (2860, 4, 616, "primitive:int", 0),
            (2864, 4, 683, "primitive:int", 0),
            (2868, 4, 712, "primitive:int", -1),
            (2872, 4, 741, "primitive:int", 0),
            (2876, 4, 773, "primitive:int", 0),
            (2880, 4, 810, "primitive:int", 0),
        ),
    },
)
