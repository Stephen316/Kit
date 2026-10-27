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
        "Contents/Config-0": (
            (22416, 4, 140, "primitive:long", 0),
            (22719, 4, 140, "primitive:long", 0),
            (23040, 4, 140, "primitive:long", 0),
            (23361, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2496, 4, 140, "primitive:long", 0),
            (3109, 4, 140, "primitive:long", 0),
            (3628, 4, 140, "primitive:long", 0),
            (4198, 4, 140, "primitive:long", 0),
            (4786, 4, 140, "primitive:long", 0),
            (5706, 4, 140, "primitive:long", 0),
        ),
    },
)
