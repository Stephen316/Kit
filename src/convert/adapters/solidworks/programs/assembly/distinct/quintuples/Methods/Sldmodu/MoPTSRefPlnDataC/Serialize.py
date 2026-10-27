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
        "Contents/Config-0-ResolvedFeatures": (
            (3193, 4, 13613, "primitive:long", 5),
            (3197, 4, 13784, "primitive:long", 0),
            (3203, 4, 13933, "primitive:long", 0),
            (3712, 4, 13613, "primitive:long", 5),
            (3716, 4, 13784, "primitive:long", 0),
            (3722, 4, 13933, "primitive:long", 0),
            (4282, 4, 13613, "primitive:long", 5),
            (4286, 4, 13784, "primitive:long", 0),
            (4292, 4, 13933, "primitive:long", 0),
        ),
    },
)
