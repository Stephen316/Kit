# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.LoadSmartReplacementData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (25753, 4, 13678, "primitive:long", 0),
            (25757, 4, 13678, "primitive:long", 0),
            (25761, 4, 13678, "primitive:long", 0),
            (25765, 4, 13698, "primitive:long", 0),
            (25777, 4, 136, "primitive:long", 0),
        ),
    },
)
