# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.MgVectorC.Restore import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (565, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (573, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (589, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (597, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (613, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (621, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
        "Contents/Config-0": (
            (19705, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (19713, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (22367, 8, 28, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (22375, 8, 41, "primitive:double", float.fromhex("0x1.c666666666666p+2")),
            (22688, 8, 28, "primitive:double", float.fromhex("-0x1.b333333333333p+1")),
            (22696, 8, 41, "primitive:double", float.fromhex("0x1.8666666666666p+2")),
            (23009, 8, 28, "primitive:double", float.fromhex("-0x1.2666666666666p+3")),
            (23017, 8, 41, "primitive:double", float.fromhex("0x1.b333333333333p+1")),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (3146, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3154, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (3640, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3648, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4210, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4218, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
