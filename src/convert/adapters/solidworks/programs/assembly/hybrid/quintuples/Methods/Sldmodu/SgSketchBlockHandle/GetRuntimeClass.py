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
        "Contents/Config-0": (
            (26008, 4, 3099, "primitive:long", 0),
            (26014, 4, 3154, "primitive:long", 0),
            (26018, 4, 4083, "primitive:ulong", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (5228, 4, 15839, "primitive:long", 0),
            (5232, 4, 16002, "primitive:long", 0),
            (5236, 4, 16657, "primitive:long", 0),
        ),
    },
)
