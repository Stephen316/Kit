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
            (24888, 4, 771, "primitive:long", 2),
            (24892, 2, 806, "primitive:ushort", 3),
            (24902, 4, 1314, "primitive:long", 0),
            (24906, 4, 1373, "primitive:long", 0),
            (25143, 4, 1565, "primitive:long", 1),
            (25155, 4, 1727, "primitive:long", 0),
            (25159, 4, 1823, "primitive:long", -1),
        ),
    },
)
