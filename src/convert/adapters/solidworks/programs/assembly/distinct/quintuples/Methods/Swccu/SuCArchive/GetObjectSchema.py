# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.GetObjectSchema import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (2, 2, 119, "primitive:ushort", 1),
            (4, 2, 139, "primitive:ushort", 20),
        ),
        "Contents/Config-0": (
            (2, 2, 119, "primitive:ushort", 1),
            (4, 2, 139, "primitive:ushort", 12),
        ),
        "Contents/Config-0-ModelHeader": (
            (2, 2, 119, "primitive:ushort", 1),
            (4, 2, 139, "primitive:ushort", 10),
        ),
    },
)
