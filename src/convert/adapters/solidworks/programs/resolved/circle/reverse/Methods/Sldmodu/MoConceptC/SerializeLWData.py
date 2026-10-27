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
            (972, 4, 259, "primitive:long", 0),
            (1171, 4, 259, "primitive:long", 0),
            (1374, 4, 259, "primitive:long", 0),
            (1576, 4, 259, "primitive:long", 0),
            (1648, 4, 259, "primitive:long", 0),
            (1843, 4, 259, "primitive:long", 0),
            (2238, 4, 259, "primitive:long", 0),
            (2456, 4, 259, "primitive:long", 0),
            (2666, 4, 259, "primitive:long", 0),
            (2860, 4, 259, "primitive:long", 0),
            (3089, 4, 259, "primitive:long", 0),
            (3294, 4, 259, "primitive:long", 0),
            (3813, 4, 259, "primitive:long", 0),
            (4383, 4, 259, "primitive:long", 0),
            (4971, 4, 259, "primitive:long", 0),
            (5900, 4, 259, "primitive:long", 0),
            (9513, 4, 259, "primitive:long", 0),
        ),
    },
)
