# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoConceptC.SerializeLWData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (72, 4, 259, "primitive:long", 0),
            (271, 4, 259, "primitive:long", 0),
            (473, 4, 259, "primitive:long", 0),
            (1448, 4, 259, "primitive:long", 0),
            (1647, 4, 259, "primitive:long", 0),
            (1850, 4, 259, "primitive:long", 0),
            (2052, 4, 259, "primitive:long", 0),
            (2124, 4, 259, "primitive:long", 0),
            (2319, 4, 259, "primitive:long", 0),
            (2714, 4, 259, "primitive:long", 0),
            (2932, 4, 259, "primitive:long", 0),
            (3142, 4, 259, "primitive:long", 0),
            (3336, 4, 259, "primitive:long", 0),
            (3565, 4, 259, "primitive:long", 0),
            (3770, 4, 259, "primitive:long", 0),
            (4289, 4, 259, "primitive:long", 0),
            (4859, 4, 259, "primitive:long", 0),
            (5447, 4, 259, "primitive:long", 0),
            (6376, 4, 259, "primitive:long", 0),
            (8583, 4, 259, "primitive:long", 0),
            (11587, 4, 259, "primitive:long", 0),
            (13731, 4, 259, "primitive:long", 0),
            (16736, 4, 259, "primitive:long", 0),
            (17914, 4, 259, "primitive:long", 0),
        ),
    },
)
