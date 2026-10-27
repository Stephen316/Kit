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
            (3557, 4, 13613, "primitive:long", 5),
            (3561, 4, 13784, "primitive:long", 0),
            (3567, 4, 13933, "primitive:long", 0),
            (4076, 4, 13613, "primitive:long", 5),
            (4080, 4, 13784, "primitive:long", 0),
            (4086, 4, 13933, "primitive:long", 0),
            (4646, 4, 13613, "primitive:long", 5),
            (4650, 4, 13784, "primitive:long", 0),
            (4656, 4, 13933, "primitive:long", 0),
            (8915, 4, 3177, "primitive:long", 0),
            (8919, 4, 3190, "primitive:long", 0),
            (8929, 4, 3307, "primitive:long", 0),
        ),
    },
)
