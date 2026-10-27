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
        "ResolvedFeatures": (
            (3427, 4, 100, "primitive:long", 0),
            (3431, 4, 100, "primitive:long", 0),
            (3445, 4, 100, "primitive:long", 0),
            (3471, 4, 100, "primitive:long", 0),
            (3946, 4, 100, "primitive:long", 0),
            (3950, 4, 100, "primitive:long", 0),
            (3964, 4, 100, "primitive:long", 0),
            (3990, 4, 100, "primitive:long", 0),
            (4516, 4, 100, "primitive:long", 0),
            (4520, 4, 100, "primitive:long", 0),
            (4534, 4, 100, "primitive:long", 0),
            (4560, 4, 100, "primitive:long", 0),
            (9372, 4, 100, "primitive:long", 1),
            (9380, 4, 100, "primitive:long", 0),
            (9398, 4, 100, "primitive:long", 0),
            (10163, 4, 100, "primitive:long", 0),
            (10391, 4, 100, "primitive:long", 0),
            (10542, 4, 100, "primitive:long", 0),
            (11630, 4, 100, "primitive:long", 0),
            (11634, 4, 100, "primitive:long", 0),
        ),
    },
)
