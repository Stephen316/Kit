# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.GcCurvatureObjectC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2278, 8, 140, "primitive:double", float.fromhex("0x1.f400000000000p+9")),
            (2286, 8, 140, "primitive:double", float.fromhex("0x1.f99999999999ap+4")),
            (2294, 8, 140, "primitive:double", float.fromhex("0x1.0000000000000p+2")),
            (2302, 8, 140, "primitive:double", float.fromhex("0x1.3333333333333p+0")),
            (2310, 8, 140, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2318, 4, 182, "primitive:ulong", 1635062320),
            (2322, 4, 195, "primitive:ulong", 31269705),
        ),
    },
)
