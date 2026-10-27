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
            (24202, 4, 771, "primitive:long", 1),
            (24206, 2, 806, "primitive:ushort", 3),
            (24216, 4, 1314, "primitive:long", 0),
            (24220, 4, 1373, "primitive:long", 0),
            (24457, 4, 1565, "primitive:long", 1),
            (24469, 4, 1727, "primitive:long", 0),
            (24473, 4, 1823, "primitive:long", -1),
        ),
    },
)
