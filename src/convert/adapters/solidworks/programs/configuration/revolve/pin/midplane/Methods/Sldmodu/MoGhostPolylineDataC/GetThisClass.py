# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoGhostPolylineDataC.GetThisClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2962, 4, 855, "primitive:long", 10001),
            (2966, 4, 893, "primitive:long", 536870913),
            (2970, 4, 1579, "primitive:long", 10001),
            (2974, 4, 1592, "primitive:long", 20),
            (2978, 4, 1612, "primitive:long", 0),
            (2982, 4, 1632, "primitive:long", -1),
            (2986, 4, 1670, "primitive:long", 1),
            (2990, 4, 1700, "primitive:long", -1),
            (2994, 4, 1783, "primitive:long", 0),
            (2998, 4, 1876, "primitive:long", 0),
        ),
    },
)
