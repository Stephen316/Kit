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
            (2363, 4, 140, "primitive:long", 0),
            (3655, 4, 140, "primitive:long", 0),
            (4174, 4, 140, "primitive:long", 0),
            (4744, 4, 140, "primitive:long", 0),
            (5332, 4, 140, "primitive:long", 0),
            (6261, 4, 140, "primitive:long", 0),
            (8470, 4, 140, "primitive:long", 0),
            (11472, 4, 140, "primitive:long", 0),
            (13725, 4, 140, "primitive:long", 0),
        ),
    },
)
