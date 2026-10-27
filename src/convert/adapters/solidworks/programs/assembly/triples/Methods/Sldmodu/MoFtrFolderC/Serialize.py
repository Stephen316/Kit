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
            (2179, 4, 281, "primitive:long", 0),
            (2183, 4, 350, "primitive:long", 0),
            (2187, 4, 429, "primitive:long", 1),
            (2191, 4, 484, "primitive:long", 1),
            (2195, 4, 281, "primitive:long", 1),
            (2199, 4, 350, "primitive:long", 0),
            (2203, 4, 429, "primitive:long", 1),
            (2207, 4, 484, "primitive:long", 1),
        ),
    },
)
