# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.UiLFConfigC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (4497, 2, 163, "primitive:short", 0),
            (4529, 2, 163, "primitive:short", 0),
            (4941, 2, 163, "primitive:short", 0),
            (4973, 2, 163, "primitive:short", 0),
            (5443, 2, 163, "primitive:short", 0),
            (5475, 2, 163, "primitive:short", 0),
            (5941, 2, 163, "primitive:short", 0),
            (5973, 2, 163, "primitive:short", 0),
            (6447, 2, 163, "primitive:short", 0),
            (6479, 2, 163, "primitive:short", 0),
            (6949, 2, 163, "primitive:short", 0),
            (6981, 2, 163, "primitive:short", 0),
            (7463, 2, 163, "primitive:short", 0),
            (7495, 2, 163, "primitive:short", 0),
            (8001, 2, 163, "primitive:short", 0),
            (8033, 2, 163, "primitive:short", 0),
            (8441, 2, 163, "primitive:short", 0),
            (8473, 2, 163, "primitive:short", 0),
            (8959, 2, 163, "primitive:short", 0),
            (8991, 2, 163, "primitive:short", 0),
        ),
    },
)
