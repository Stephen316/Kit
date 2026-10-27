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
            (21324, 4, 140, "primitive:long", 0),
            (21627, 4, 140, "primitive:long", 0),
            (21948, 4, 140, "primitive:long", 0),
            (22269, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2272, 4, 140, "primitive:long", 0),
            (2885, 4, 140, "primitive:long", 0),
            (3404, 4, 140, "primitive:long", 0),
            (3974, 4, 140, "primitive:long", 0),
            (4562, 4, 140, "primitive:long", 0),
            (5482, 4, 140, "primitive:long", 0),
        ),
    },
)
