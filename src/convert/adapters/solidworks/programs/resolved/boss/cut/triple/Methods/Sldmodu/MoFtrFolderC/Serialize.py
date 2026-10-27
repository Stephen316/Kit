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
            (2690, 4, 281, "primitive:long", 0),
            (2694, 4, 350, "primitive:long", 0),
            (2698, 4, 429, "primitive:long", 1),
            (2702, 4, 484, "primitive:long", 1),
            (2706, 4, 281, "primitive:long", 1),
            (2710, 4, 350, "primitive:long", 0),
            (2714, 4, 429, "primitive:long", 1),
            (2718, 4, 484, "primitive:long", 1),
        ),
    },
)
