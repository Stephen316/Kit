# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2839, 4, 100, "primitive:long", 0),
            (2843, 4, 100, "primitive:long", 0),
            (2857, 4, 100, "primitive:long", 0),
            (2883, 4, 100, "primitive:long", 0),
            (3358, 4, 100, "primitive:long", 0),
            (3362, 4, 100, "primitive:long", 0),
            (3376, 4, 100, "primitive:long", 0),
            (3402, 4, 100, "primitive:long", 0),
            (3928, 4, 100, "primitive:long", 0),
            (3932, 4, 100, "primitive:long", 0),
            (3946, 4, 100, "primitive:long", 0),
            (3972, 4, 100, "primitive:long", 0),
        ),
    },
)
