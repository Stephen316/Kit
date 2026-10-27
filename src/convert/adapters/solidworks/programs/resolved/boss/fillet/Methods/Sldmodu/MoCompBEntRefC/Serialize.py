# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompBEntRefC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (11852, 1, 1211, "primitive:uchar", 0),
            (13870, 1, 1211, "primitive:uchar", 0),
            (14109, 1, 1211, "primitive:uchar", 0),
            (14369, 1, 1211, "primitive:uchar", 0),
            (14709, 1, 1211, "primitive:uchar", 0),
        ),
    },
)
