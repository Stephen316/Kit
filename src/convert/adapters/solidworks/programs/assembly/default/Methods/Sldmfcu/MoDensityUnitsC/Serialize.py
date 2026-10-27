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
            (1384, 2, 208, "primitive:ushort", 3),
            (1386, 2, 261, "primitive:ushort", 1),
            (1388, 1, 307, "primitive:uchar", 0),
            (1389, 2, 431, "primitive:ushort", 3),
            (1391, 4, 461, "primitive:int", 0),
        ),
    },
)
