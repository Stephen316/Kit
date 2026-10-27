# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Slduiu.UiModelDocC.ReplaceCompIdInDisplayDataMap import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Definition": (
            (20, 4, 1978, "primitive:ulong", 2208513334),
            (24, 2, 1992, "primitive:ushort", 10181),
            (26, 2, 2006, "primitive:ushort", 4558),
        ),
    },
)
