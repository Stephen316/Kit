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
            (7958, 4, 126, "primitive:long", 2),
            (8540, 4, 126, "primitive:long", 32),
            (8591, 4, 126, "primitive:long", 32),
            (8611, 4, 126, "primitive:long", 32),
            (8631, 4, 126, "primitive:long", 32),
            (8651, 4, 126, "primitive:long", 32),
            (8733, 4, 126, "primitive:long", 32),
            (8757, 4, 126, "primitive:long", 32),
            (8777, 4, 126, "primitive:long", 32),
            (8797, 4, 126, "primitive:long", 32),
            (8817, 4, 126, "primitive:long", 32),
        ),
    },
)
