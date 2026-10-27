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
            (1976, 4, 281, "primitive:long", 0),
            (1980, 4, 350, "primitive:long", 0),
            (1984, 4, 429, "primitive:long", 1),
            (1988, 4, 484, "primitive:long", 1),
            (1992, 4, 281, "primitive:long", 1),
            (1996, 4, 350, "primitive:long", 0),
            (2000, 4, 429, "primitive:long", 1),
            (2004, 4, 484, "primitive:long", 1),
        ),
    },
)
