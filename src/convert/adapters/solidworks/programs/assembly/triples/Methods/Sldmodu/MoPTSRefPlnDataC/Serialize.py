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
            (3081, 4, 13613, "primitive:long", 5),
            (3085, 4, 13784, "primitive:long", 0),
            (3091, 4, 13933, "primitive:long", 0),
            (3600, 4, 13613, "primitive:long", 5),
            (3604, 4, 13784, "primitive:long", 0),
            (3610, 4, 13933, "primitive:long", 0),
            (4170, 4, 13613, "primitive:long", 5),
            (4174, 4, 13784, "primitive:long", 0),
            (4180, 4, 13933, "primitive:long", 0),
        ),
    },
)
