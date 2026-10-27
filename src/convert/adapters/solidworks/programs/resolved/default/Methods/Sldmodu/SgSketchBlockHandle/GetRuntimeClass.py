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
            (5592, 4, 15839, "primitive:long", 0),
            (5596, 4, 16002, "primitive:long", 0),
            (5600, 4, 16657, "primitive:long", 0),
            (7713, 4, 15839, "primitive:long", 0),
            (7717, 4, 16002, "primitive:long", 0),
            (7721, 4, 16657, "primitive:long", 0),
        ),
    },
)
