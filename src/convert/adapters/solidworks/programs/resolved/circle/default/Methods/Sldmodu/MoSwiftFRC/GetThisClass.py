# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSwiftFRC.GetThisClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (763, 4, 126, "primitive:long", 26),
            (882, 4, 126, "primitive:long", 33),
            (5758, 4, 126, "primitive:long", 2),
            (6549, 4, 126, "primitive:long", 5),
            (9364, 4, 126, "primitive:long", 2),
            (9944, 4, 126, "primitive:long", 33),
            (9995, 4, 126, "primitive:long", 33),
            (10077, 4, 126, "primitive:long", 33),
            (10101, 4, 126, "primitive:long", 33),
        ),
    },
)
