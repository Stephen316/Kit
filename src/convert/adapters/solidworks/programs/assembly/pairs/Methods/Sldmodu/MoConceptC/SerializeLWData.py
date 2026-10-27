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
        "Contents/CMgr": (
            (48, 4, 259, "primitive:long", 0),
            (244, 4, 259, "primitive:long", 0),
        ),
        "Contents/Config-0": (
            (22, 4, 864, "primitive:long", 0),
            (26, 4, 923, "primitive:ulong", 18000),
            (84, 4, 259, "primitive:long", 1),
            (197, 4, 259, "primitive:long", 0),
            (850, 4, 259, "primitive:long", 0),
            (21039, 4, 259, "primitive:long", 0),
            (21109, 4, 259, "primitive:long", 0),
            (21412, 4, 259, "primitive:long", 0),
            (21733, 4, 259, "primitive:long", 0),
            (22054, 4, 259, "primitive:long", 0),
            (24547, 4, 259, "primitive:long", 0),
            (24865, 4, 259, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (72, 4, 259, "primitive:long", 0),
            (271, 4, 259, "primitive:long", 0),
            (473, 4, 259, "primitive:long", 0),
            (893, 4, 259, "primitive:long", 0),
            (1092, 4, 259, "primitive:long", 0),
            (1314, 4, 259, "primitive:long", 0),
            (1521, 4, 259, "primitive:long", 0),
            (1723, 4, 259, "primitive:long", 0),
            (1795, 4, 259, "primitive:long", 0),
            (1990, 4, 259, "primitive:long", 0),
            (2371, 4, 259, "primitive:long", 0),
            (2565, 4, 259, "primitive:long", 0),
            (2762, 4, 259, "primitive:long", 0),
            (3281, 4, 259, "primitive:long", 0),
            (3851, 4, 259, "primitive:long", 0),
            (4439, 4, 259, "primitive:long", 0),
            (5359, 4, 259, "primitive:long", 0),
        ),
    },
)
