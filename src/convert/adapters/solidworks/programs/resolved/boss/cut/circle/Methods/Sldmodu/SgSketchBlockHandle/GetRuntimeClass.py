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
            (6068, 4, 15839, "primitive:long", 0),
            (6072, 4, 16002, "primitive:long", 0),
            (6076, 4, 16657, "primitive:long", 0),
            (8189, 4, 15839, "primitive:long", 0),
            (8193, 4, 16002, "primitive:long", 0),
            (8197, 4, 16657, "primitive:long", 0),
            (13364, 4, 15839, "primitive:long", 0),
            (13368, 4, 16002, "primitive:long", 0),
            (13372, 4, 16657, "primitive:long", 0),
            (17570, 4, 15839, "primitive:long", 0),
            (17574, 4, 16002, "primitive:long", 0),
            (17578, 4, 16657, "primitive:long", 0),
        ),
    },
)
