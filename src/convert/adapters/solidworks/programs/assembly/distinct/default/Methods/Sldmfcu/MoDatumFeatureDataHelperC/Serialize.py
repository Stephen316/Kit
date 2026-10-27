# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoDatumFeatureDataHelperC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (18837, 1, 188, "primitive:uchar", 0),
            (18838, 1, 210, "primitive:uchar", 0),
            (18839, 1, 232, "primitive:uchar", 0),
            (18840, 4, 253, "primitive:int", 0),
            (18844, 4, 266, "primitive:int", 0),
            (18856, 4, 322, "primitive:int", 0),
            (18860, 4, 335, "primitive:int", 0),
            (18864, 4, 348, "primitive:int", 0),
        ),
    },
)
