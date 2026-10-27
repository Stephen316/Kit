# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFtrFolderC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2123, 4, 281, "primitive:long", 0),
            (2127, 4, 350, "primitive:long", 0),
            (2131, 4, 429, "primitive:long", 1),
            (2135, 4, 484, "primitive:long", 1),
            (2139, 4, 281, "primitive:long", 1),
            (2143, 4, 350, "primitive:long", 0),
            (2147, 4, 429, "primitive:long", 1),
            (2151, 4, 484, "primitive:long", 1),
        ),
    },
)
