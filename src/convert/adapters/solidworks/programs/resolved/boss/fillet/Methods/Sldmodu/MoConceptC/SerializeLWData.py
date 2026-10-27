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
            (1091, 4, 259, "primitive:long", 0),
            (1290, 4, 259, "primitive:long", 0),
            (1493, 4, 259, "primitive:long", 0),
            (1695, 4, 259, "primitive:long", 0),
            (1767, 4, 259, "primitive:long", 0),
            (1962, 4, 259, "primitive:long", 0),
            (2357, 4, 259, "primitive:long", 0),
            (2575, 4, 259, "primitive:long", 0),
            (2785, 4, 259, "primitive:long", 0),
            (2979, 4, 259, "primitive:long", 0),
            (3208, 4, 259, "primitive:long", 0),
            (3413, 4, 259, "primitive:long", 0),
            (3932, 4, 259, "primitive:long", 0),
            (4502, 4, 259, "primitive:long", 0),
            (5090, 4, 259, "primitive:long", 0),
            (6019, 4, 259, "primitive:long", 0),
            (8226, 4, 259, "primitive:long", 0),
            (11242, 4, 259, "primitive:long", 0),
        ),
    },
)
