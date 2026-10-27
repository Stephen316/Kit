# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5312, 4, 4724, "primitive:ulong", 0),
            (5316, 4, 4744, "primitive:long", 0),
            (5320, 4, 1931, "primitive:long", 3),
            (5325, 4, 2342, "primitive:long", 0),
            (5335, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
