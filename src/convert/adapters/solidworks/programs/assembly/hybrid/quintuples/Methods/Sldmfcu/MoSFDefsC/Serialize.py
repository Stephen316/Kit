# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSFDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (11773, 4, 167, "primitive:int", 0),
            (11777, 4, 188, "primitive:int", 2),
            (11781, 8, 208, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (11789, 8, 221, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
        ),
    },
)
