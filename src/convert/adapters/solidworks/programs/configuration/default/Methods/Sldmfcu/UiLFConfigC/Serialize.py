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
            (4467, 2, 163, "primitive:short", 0),
            (4499, 2, 163, "primitive:short", 0),
            (4911, 2, 163, "primitive:short", 0),
            (4943, 2, 163, "primitive:short", 0),
            (5413, 2, 163, "primitive:short", 0),
            (5445, 2, 163, "primitive:short", 0),
            (5911, 2, 163, "primitive:short", 0),
            (5943, 2, 163, "primitive:short", 0),
            (6417, 2, 163, "primitive:short", 0),
            (6449, 2, 163, "primitive:short", 0),
            (6919, 2, 163, "primitive:short", 0),
            (6951, 2, 163, "primitive:short", 0),
            (7433, 2, 163, "primitive:short", 0),
            (7465, 2, 163, "primitive:short", 0),
            (7971, 2, 163, "primitive:short", 0),
            (8003, 2, 163, "primitive:short", 0),
            (8411, 2, 163, "primitive:short", 0),
            (8443, 2, 163, "primitive:short", 0),
            (8929, 2, 163, "primitive:short", 0),
            (8961, 2, 163, "primitive:short", 0),
        ),
    },
)
