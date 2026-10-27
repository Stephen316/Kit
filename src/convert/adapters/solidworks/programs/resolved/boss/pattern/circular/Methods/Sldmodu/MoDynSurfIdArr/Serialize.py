# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDynSurfIdArr.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9237, 4, 4151, "primitive:long", 0),
            (9241, 4, 4164, "primitive:long", 0),
            (9430, 4, 4151, "primitive:long", 1),
            (9434, 4, 4164, "primitive:long", 0),
            (12181, 4, 4151, "primitive:long", 0),
            (12185, 4, 4164, "primitive:long", 0),
            (12225, 4, 4151, "primitive:long", 1),
            (12229, 4, 4164, "primitive:long", 0),
            (17641, 4, 4151, "primitive:long", 1),
            (17645, 4, 4164, "primitive:long", 0),
            (17665, 4, 4151, "primitive:long", 0),
            (17669, 4, 4164, "primitive:long", 0),
        ),
    },
)
