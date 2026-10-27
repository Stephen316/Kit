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
            (4836, 2, 13751, "primitive:ushort", 31),
            (4854, 2, 13906, "primitive:ushort", 1),
            (4856, 2, 13996, "primitive:ushort", 0),
            (4862, 2, 14480, "primitive:ushort", 0),
            (4864, 4, 14546, "primitive:long", -2),
            (4900, 2, 14739, "primitive:ushort", 0),
            (4902, 2, 14916, "primitive:ushort", 0),
            (5240, 4, 2988, "primitive:long", 0),
        ),
    },
)
