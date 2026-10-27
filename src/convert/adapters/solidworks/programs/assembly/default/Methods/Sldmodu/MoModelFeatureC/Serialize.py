# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoModelFeatureC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (20638, 4, 140, "primitive:long", 0),
            (20941, 4, 140, "primitive:long", 0),
            (21262, 4, 140, "primitive:long", 0),
            (21583, 4, 140, "primitive:long", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (2216, 4, 140, "primitive:long", 0),
            (2829, 4, 140, "primitive:long", 0),
            (3348, 4, 140, "primitive:long", 0),
            (3918, 4, 140, "primitive:long", 0),
            (4506, 4, 140, "primitive:long", 0),
            (5426, 4, 140, "primitive:long", 0),
        ),
    },
)
