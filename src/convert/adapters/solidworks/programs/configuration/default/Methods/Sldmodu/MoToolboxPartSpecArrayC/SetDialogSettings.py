# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoToolboxPartSpecArrayC.SetDialogSettings import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2353, 4, 488, "primitive:long", 1),
            (2357, 4, 500, "primitive:long", 1),
            (2361, 4, 512, "primitive:ulong", 16221267),
            (2365, 4, 524, "primitive:ulong", 6759173),
            (2369, 4, 536, "primitive:long", 95),
            (2373, 4, 548, "primitive:ulong", 0),
        ),
    },
)
