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
        "ResolvedFeatures": (
            (2095, 4, 281, "primitive:long", 0),
            (2099, 4, 350, "primitive:long", 0),
            (2103, 4, 429, "primitive:long", 1),
            (2107, 4, 484, "primitive:long", 1),
            (2111, 4, 281, "primitive:long", 1),
            (2115, 4, 350, "primitive:long", 0),
            (2119, 4, 429, "primitive:long", 1),
            (2123, 4, 484, "primitive:long", 1),
        ),
    },
)
