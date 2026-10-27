# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFtrFolderC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2452, 4, 281, "primitive:long", 0),
            (2456, 4, 350, "primitive:long", 0),
            (2460, 4, 429, "primitive:long", 1),
            (2464, 4, 484, "primitive:long", 1),
            (2468, 4, 281, "primitive:long", 1),
            (2472, 4, 350, "primitive:long", 0),
            (2476, 4, 429, "primitive:long", 1),
            (2480, 4, 484, "primitive:long", 1),
        ),
    },
)
