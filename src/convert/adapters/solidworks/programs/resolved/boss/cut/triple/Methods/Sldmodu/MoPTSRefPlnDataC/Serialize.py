# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPTSRefPlnDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (4271, 4, 13613, "primitive:long", 5),
            (4275, 4, 13784, "primitive:long", 0),
            (4281, 4, 13933, "primitive:long", 0),
            (4790, 4, 13613, "primitive:long", 5),
            (4794, 4, 13784, "primitive:long", 0),
            (4800, 4, 13933, "primitive:long", 0),
            (5360, 4, 13613, "primitive:long", 5),
            (5364, 4, 13784, "primitive:long", 0),
            (5370, 4, 13933, "primitive:long", 0),
            (9627, 4, 3177, "primitive:long", 0),
            (9631, 4, 3190, "primitive:long", 0),
            (9641, 4, 3307, "primitive:long", 0),
            (14951, 4, 3177, "primitive:long", 0),
            (14955, 4, 3190, "primitive:long", 0),
            (20021, 4, 3177, "primitive:long", 0),
            (20025, 4, 3190, "primitive:long", 0),
            (25095, 4, 3177, "primitive:long", 0),
            (25099, 4, 3190, "primitive:long", 0),
        ),
    },
)
