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
        "ResolvedFeatures": (
            (3622, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (3630, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (4116, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (4124, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4686, 8, 28, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (4694, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10190, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10198, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10407, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10415, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10686, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10694, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10710, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10718, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (11319, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (11327, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (11513, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (11521, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (12040, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (12048, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (12064, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (12072, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
