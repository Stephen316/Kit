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
            (2347, 4, 281, "primitive:long", 0),
            (2351, 4, 350, "primitive:long", 0),
            (2355, 4, 429, "primitive:long", 1),
            (2359, 4, 484, "primitive:long", 1),
            (2363, 4, 281, "primitive:long", 1),
            (2367, 4, 350, "primitive:long", 0),
            (2371, 4, 429, "primitive:long", 1),
            (2375, 4, 484, "primitive:long", 1),
        ),
    },
)
