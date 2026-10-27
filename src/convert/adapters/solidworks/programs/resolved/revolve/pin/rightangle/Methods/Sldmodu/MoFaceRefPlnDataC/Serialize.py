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
            (10191, 4, 7121, "primitive:long", 1),
            (10219, 8, 7292, "primitive:double", float.fromhex("0x1.9a9f6ac977a92p-5")),
            (10608, 8, 5803, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10616, 1, 5864, "primitive:uchar", 0),
        ),
    },
)
