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
            (8772, 4, 4151, "primitive:long", 0),
            (8776, 4, 4164, "primitive:long", 0),
            (8965, 4, 4151, "primitive:long", 1),
            (8969, 4, 4164, "primitive:long", 0),
            (11710, 4, 4151, "primitive:long", 0),
            (11714, 4, 4164, "primitive:long", 0),
            (11754, 4, 4151, "primitive:long", 1),
            (11758, 4, 4164, "primitive:long", 0),
            (18815, 4, 4151, "primitive:long", 1),
            (18819, 4, 4164, "primitive:long", 0),
            (18839, 4, 4151, "primitive:long", 0),
            (18843, 4, 4164, "primitive:long", 0),
        ),
    },
)
