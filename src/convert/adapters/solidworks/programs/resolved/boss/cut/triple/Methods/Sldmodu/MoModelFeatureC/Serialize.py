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
            (2839, 4, 140, "primitive:long", 0),
            (4131, 4, 140, "primitive:long", 0),
            (4650, 4, 140, "primitive:long", 0),
            (5220, 4, 140, "primitive:long", 0),
            (5808, 4, 140, "primitive:long", 0),
            (6737, 4, 140, "primitive:long", 0),
            (8946, 4, 140, "primitive:long", 0),
            (11948, 4, 140, "primitive:long", 0),
            (14094, 4, 140, "primitive:long", 0),
            (17109, 4, 140, "primitive:long", 0),
            (19244, 4, 140, "primitive:long", 0),
            (22179, 4, 140, "primitive:long", 0),
            (24314, 4, 140, "primitive:long", 0),
        ),
    },
)
