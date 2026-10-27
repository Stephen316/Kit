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
            (22554, 4, 140, "primitive:long", 0),
            (22857, 4, 140, "primitive:long", 0),
            (23178, 4, 140, "primitive:long", 0),
            (23499, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2440, 4, 140, "primitive:long", 0),
            (3053, 4, 140, "primitive:long", 0),
            (3572, 4, 140, "primitive:long", 0),
            (4142, 4, 140, "primitive:long", 0),
            (4730, 4, 140, "primitive:long", 0),
            (5650, 4, 140, "primitive:long", 0),
        ),
    },
)
