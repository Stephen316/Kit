# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5365, 2, 239, "primitive:ushort", 65534),
            (5367, 2, 334, "primitive:ushort", 0),
            (7264, 2, 239, "primitive:ushort", 65534),
            (7266, 2, 334, "primitive:ushort", 0),
            (7319, 2, 239, "primitive:ushort", 65534),
            (7321, 2, 334, "primitive:ushort", 0),
            (7374, 2, 239, "primitive:ushort", 65534),
            (7376, 2, 334, "primitive:ushort", 0),
            (7429, 2, 239, "primitive:ushort", 65534),
            (7431, 2, 334, "primitive:ushort", 0),
        ),
    },
)
