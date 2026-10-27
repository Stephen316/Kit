# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8671, 4, 370, "primitive:long", 4),
            (8691, 4, 370, "primitive:long", 3),
            (8711, 4, 370, "primitive:long", 2),
            (8731, 4, 370, "primitive:long", 1),
            (8837, 4, 370, "primitive:long", 4),
            (8857, 4, 370, "primitive:long", 1),
            (8877, 4, 370, "primitive:long", 2),
            (8897, 4, 370, "primitive:long", 3),
            (9037, 4, 370, "primitive:long", 5),
        ),
    },
)
