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
            (21950, 4, 140, "primitive:long", 0),
            (22253, 4, 140, "primitive:long", 0),
            (22574, 4, 140, "primitive:long", 0),
            (22895, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2328, 4, 140, "primitive:long", 0),
            (2941, 4, 140, "primitive:long", 0),
            (3460, 4, 140, "primitive:long", 0),
            (4030, 4, 140, "primitive:long", 0),
            (4618, 4, 140, "primitive:long", 0),
            (5538, 4, 140, "primitive:long", 0),
        ),
    },
)
