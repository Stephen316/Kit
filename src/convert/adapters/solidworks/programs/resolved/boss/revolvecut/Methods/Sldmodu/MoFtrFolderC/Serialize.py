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
            (2214, 4, 281, "primitive:long", 0),
            (2218, 4, 350, "primitive:long", 0),
            (2222, 4, 429, "primitive:long", 1),
            (2226, 4, 484, "primitive:long", 1),
            (2230, 4, 281, "primitive:long", 1),
            (2234, 4, 350, "primitive:long", 0),
            (2238, 4, 429, "primitive:long", 1),
            (2242, 4, 484, "primitive:long", 1),
        ),
    },
)
