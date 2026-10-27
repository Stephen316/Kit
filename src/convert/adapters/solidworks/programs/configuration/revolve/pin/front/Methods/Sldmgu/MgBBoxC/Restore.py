# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgBBoxC.Restore import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2376, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
            (2384, 8, 55, "primitive:double", float.fromhex("-0x1.999999999999ap-6")),
            (2392, 8, 80, "primitive:double", float.fromhex("0x0.0p+0")),
            (2400, 8, 105, "primitive:double", float.fromhex("0x1.47ae147ae147bp-9")),
            (2408, 8, 130, "primitive:double", float.fromhex("0x0.0p+0")),
            (2416, 8, 155, "primitive:double", float.fromhex("0x1.47ae147ae147bp-9")),
            (2424, 8, 180, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-9")),
            (2432, 8, 205, "primitive:double", float.fromhex("-0x1.999999999999ap-5")),
            (2440, 8, 230, "primitive:double", float.fromhex("-0x1.47ae147ae147bp-9")),
        ),
    },
)
