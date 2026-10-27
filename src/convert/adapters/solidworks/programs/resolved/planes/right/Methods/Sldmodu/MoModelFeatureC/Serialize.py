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
        "ResolvedFeatures": (
            (2125, 4, 140, "primitive:long", 0),
            (3417, 4, 140, "primitive:long", 0),
            (3936, 4, 140, "primitive:long", 0),
            (4506, 4, 140, "primitive:long", 0),
            (5094, 4, 140, "primitive:long", 0),
            (6023, 4, 140, "primitive:long", 0),
            (8304, 4, 140, "primitive:long", 0),
        ),
    },
)
