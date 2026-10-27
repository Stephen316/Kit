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
            (10392, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10400, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10609, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10617, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (10888, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10896, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10912, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (10920, 8, 41, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (11521, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (11529, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (11715, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
            (11723, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (12242, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (12250, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
            (12266, 8, 28, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
            (12274, 8, 41, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
