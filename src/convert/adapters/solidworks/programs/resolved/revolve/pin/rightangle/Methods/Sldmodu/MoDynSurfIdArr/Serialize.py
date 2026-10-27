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
            (9772, 4, 4151, "primitive:long", 0),
            (9776, 4, 4164, "primitive:long", 0),
            (9843, 4, 4151, "primitive:long", 1),
            (9847, 4, 4164, "primitive:long", 0),
            (10009, 4, 4151, "primitive:long", 1),
            (10013, 4, 4164, "primitive:long", 0),
            (10133, 4, 4151, "primitive:long", 0),
            (10137, 4, 4164, "primitive:long", 0),
        ),
    },
)
