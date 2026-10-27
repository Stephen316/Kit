# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGThreeDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4668, 2, 13751, "primitive:ushort", 31),
            (4686, 2, 13906, "primitive:ushort", 1),
            (4688, 2, 13996, "primitive:ushort", 0),
            (4694, 2, 14480, "primitive:ushort", 0),
            (4696, 4, 14546, "primitive:long", -2),
            (4732, 2, 14739, "primitive:ushort", 0),
            (4734, 2, 14916, "primitive:ushort", 0),
            (5072, 4, 2988, "primitive:long", 0),
        ),
    },
)
