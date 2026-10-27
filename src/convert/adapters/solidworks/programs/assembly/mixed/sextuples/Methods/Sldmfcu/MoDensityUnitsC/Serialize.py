# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDensityUnitsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (3322, 2, 208, "primitive:ushort", 3),
            (3324, 2, 261, "primitive:ushort", 1),
            (3326, 1, 307, "primitive:uchar", 0),
            (3327, 2, 431, "primitive:ushort", 3),
            (3329, 4, 461, "primitive:int", 0),
        ),
    },
)
