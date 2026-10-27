# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9573, 4, 370, "primitive:long", 2),
            (9593, 4, 370, "primitive:long", 3),
            (9615, 4, 370, "primitive:long", 5),
            (9697, 4, 370, "primitive:long", 3),
            (9717, 4, 370, "primitive:long", 4),
            (9739, 4, 370, "primitive:long", 2),
            (9875, 4, 370, "primitive:long", 5),
        ),
    },
)
