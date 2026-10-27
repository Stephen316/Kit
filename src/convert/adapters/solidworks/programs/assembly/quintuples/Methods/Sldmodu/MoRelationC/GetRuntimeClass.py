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
        "Contents/Config-0": (
            (5264, 4, 3454, "primitive:long", 0),
            (5272, 4, 3580, "primitive:long", 1),
            (5276, 4, 3674, "primitive:long", -1),
            (5282, 4, 3851, "primitive:long", -1),
            (5286, 4, 3872, "primitive:long", 0),
        ),
    },
)
