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
            (3025, 4, 13613, "primitive:long", 5),
            (3029, 4, 13784, "primitive:long", 0),
            (3035, 4, 13933, "primitive:long", 0),
            (3544, 4, 13613, "primitive:long", 5),
            (3548, 4, 13784, "primitive:long", 0),
            (3554, 4, 13933, "primitive:long", 0),
            (4114, 4, 13613, "primitive:long", 5),
            (4118, 4, 13784, "primitive:long", 0),
            (4124, 4, 13933, "primitive:long", 0),
        ),
    },
)
