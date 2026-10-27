# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoModelFeatureC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2244, 4, 140, "primitive:long", 0),
            (3536, 4, 140, "primitive:long", 0),
            (4055, 4, 140, "primitive:long", 0),
            (4625, 4, 140, "primitive:long", 0),
            (5213, 4, 140, "primitive:long", 0),
            (6142, 4, 140, "primitive:long", 0),
            (8923, 4, 140, "primitive:long", 0),
            (11951, 4, 140, "primitive:long", 0),
        ),
    },
)
