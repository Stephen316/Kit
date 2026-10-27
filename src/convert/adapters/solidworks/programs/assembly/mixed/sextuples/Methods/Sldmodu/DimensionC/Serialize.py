# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.DimensionC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5018, 4, 1100, "primitive:long", 0),
            (5026, 4, 1380, "primitive:long", -1),
            (5030, 4, 1530, "primitive:long", 0),
            (5034, 4, 1592, "primitive:long", 0),
            (5038, 4, 1658, "primitive:long", 0),
            (5044, 2, 1826, "primitive:ushort", 0),
            (5046, 1, 1895, "primitive:uchar", 0),
        ),
    },
)
