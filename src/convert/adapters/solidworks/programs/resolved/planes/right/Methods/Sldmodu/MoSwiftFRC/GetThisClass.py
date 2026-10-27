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
            (882, 4, 126, "primitive:long", 32),
            (5758, 4, 126, "primitive:long", 2),
            (7958, 4, 126, "primitive:long", 4),
            (8612, 4, 126, "primitive:long", 32),
            (8663, 4, 126, "primitive:long", 32),
            (8683, 4, 126, "primitive:long", 32),
            (8703, 4, 126, "primitive:long", 32),
            (8723, 4, 126, "primitive:long", 32),
            (8805, 4, 126, "primitive:long", 32),
            (8829, 4, 126, "primitive:long", 32),
            (8849, 4, 126, "primitive:long", 32),
            (8869, 4, 126, "primitive:long", 32),
            (8889, 4, 126, "primitive:long", 32),
        ),
    },
)
