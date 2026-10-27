# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9568, 4, 7121, "primitive:long", 1),
            (9596, 8, 7292, "primitive:double", float.fromhex("0x1.91530bd7c536fp-7")),
            (
                17867,
                8,
                5803,
                "primitive:double",
                float.fromhex("-0x1.0000000000000p+0"),
            ),
            (17875, 1, 5864, "primitive:uchar", 0),
        ),
    },
)
