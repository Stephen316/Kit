# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoMassPropCacheC.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (24705, 4, 815, "primitive:long", 1),
            (24709, 4, 862, "primitive:long", 101),
            (24713, 4, 875, "primitive:long", 103),
            (24717, 8, 888, "primitive:double", float.fromhex("0x1.f400000000000p+9")),
        ),
    },
)
