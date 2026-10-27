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
            (4033, 4, 13613, "primitive:long", 5),
            (4037, 4, 13784, "primitive:long", 0),
            (4043, 4, 13933, "primitive:long", 0),
            (4552, 4, 13613, "primitive:long", 5),
            (4556, 4, 13784, "primitive:long", 0),
            (4562, 4, 13933, "primitive:long", 0),
            (5122, 4, 13613, "primitive:long", 5),
            (5126, 4, 13784, "primitive:long", 0),
            (5132, 4, 13933, "primitive:long", 0),
            (9389, 4, 3177, "primitive:long", 0),
            (9393, 4, 3190, "primitive:long", 0),
            (9403, 4, 3307, "primitive:long", 0),
            (14701, 4, 3177, "primitive:long", 0),
            (14705, 4, 3190, "primitive:long", 0),
            (19024, 4, 3177, "primitive:long", 0),
            (19028, 4, 3190, "primitive:long", 0),
        ),
    },
)
