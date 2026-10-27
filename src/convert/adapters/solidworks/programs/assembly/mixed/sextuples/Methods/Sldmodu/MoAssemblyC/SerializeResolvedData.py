# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.SerializeResolvedData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (25980, 4, 771, "primitive:long", 6),
            (25984, 2, 806, "primitive:ushort", 3),
            (25994, 4, 1314, "primitive:long", 0),
            (25998, 4, 1373, "primitive:long", 0),
            (26235, 4, 1565, "primitive:long", 1),
            (26247, 4, 1727, "primitive:long", 0),
            (26251, 4, 1823, "primitive:long", -1),
        ),
    },
)
