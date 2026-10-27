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
            (882, 4, 126, "primitive:long", 34),
            (5758, 4, 126, "primitive:long", 2),
            (6904, 4, 126, "primitive:long", 5),
            (11811, 4, 126, "primitive:long", 2),
            (12391, 4, 126, "primitive:long", 34),
            (12442, 4, 126, "primitive:long", 34),
            (12462, 4, 126, "primitive:long", 34),
            (12482, 4, 126, "primitive:long", 34),
            (12502, 4, 126, "primitive:long", 34),
            (12584, 4, 126, "primitive:long", 34),
            (12608, 4, 126, "primitive:long", 34),
            (12628, 4, 126, "primitive:long", 34),
            (12648, 4, 126, "primitive:long", 34),
            (12668, 4, 126, "primitive:long", 34),
        ),
    },
)
