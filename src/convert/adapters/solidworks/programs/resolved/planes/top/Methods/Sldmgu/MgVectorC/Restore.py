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
            (9265, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9273, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (9544, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9552, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (9568, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (9576, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10060, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10068, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10084, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (10092, 8, 41, "primitive:double", float.fromhex("-0x0.0p+0")),
            (10168, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (10176, 8, 41, "primitive:double", float.fromhex("-0x0.0p+0")),
            (10362, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10370, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
        ),
    },
)
