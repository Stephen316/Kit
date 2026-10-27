# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRelationC.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (3026, 4, 3454, "primitive:long", 0),
            (3034, 4, 3580, "primitive:long", 1),
            (3038, 4, 3674, "primitive:long", -1),
            (3044, 4, 3851, "primitive:long", -1),
            (3048, 4, 3872, "primitive:long", 0),
        ),
    },
)
