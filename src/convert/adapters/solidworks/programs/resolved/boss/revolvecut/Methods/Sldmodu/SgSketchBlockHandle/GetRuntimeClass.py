# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5830, 4, 15839, "primitive:long", 0),
            (5834, 4, 16002, "primitive:long", 0),
            (5838, 4, 16657, "primitive:long", 0),
            (7951, 4, 15839, "primitive:long", 0),
            (7955, 4, 16002, "primitive:long", 0),
            (7959, 4, 16657, "primitive:long", 0),
            (14256, 4, 15839, "primitive:long", 0),
            (14260, 4, 16002, "primitive:long", 0),
            (14264, 4, 16657, "primitive:long", 0),
        ),
    },
)
