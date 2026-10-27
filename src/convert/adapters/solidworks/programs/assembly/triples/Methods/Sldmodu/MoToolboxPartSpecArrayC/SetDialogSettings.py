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
        "Contents/Config-0": (
            (3809, 4, 488, "primitive:long", 1),
            (3813, 4, 500, "primitive:long", 1),
            (3817, 4, 512, "primitive:ulong", 16221267),
            (3821, 4, 524, "primitive:ulong", 6759173),
            (3825, 4, 536, "primitive:long", 95),
            (3829, 4, 548, "primitive:ulong", 0),
        ),
    },
)
