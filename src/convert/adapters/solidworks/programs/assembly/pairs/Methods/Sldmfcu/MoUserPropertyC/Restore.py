# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoUserPropertyC.Restore import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (1496, 4, 35, "primitive:ulong", 0),
            (21334, 4, 35, "primitive:ulong", 0),
            (21645, 4, 35, "primitive:ulong", 0),
            (21966, 4, 35, "primitive:ulong", 0),
            (22287, 4, 35, "primitive:ulong", 0),
        ),
    },
)
