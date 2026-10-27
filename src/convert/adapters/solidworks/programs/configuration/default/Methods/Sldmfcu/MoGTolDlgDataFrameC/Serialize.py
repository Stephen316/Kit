# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoGTolDlgDataFrameC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (17700, 1, 492, "primitive:uchar", 0),
            (17709, 1, 538, "primitive:uchar", 0),
            (17730, 4, 963, "primitive:int", 0),
            (17734, 4, 976, "primitive:int", 0),
            (17738, 2, 1007, "primitive:ushort", 0),
            (17744, 4, 1131, "primitive:int", 0),
            (17752, 1, 492, "primitive:uchar", 0),
            (17761, 1, 538, "primitive:uchar", 0),
            (17782, 4, 963, "primitive:int", 0),
            (17786, 4, 976, "primitive:int", 0),
            (17790, 2, 1007, "primitive:ushort", 0),
            (17796, 4, 1131, "primitive:int", 0),
        ),
    },
)
