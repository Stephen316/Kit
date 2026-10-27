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
            (19929, 1, 188, "primitive:uchar", 0),
            (19930, 1, 210, "primitive:uchar", 0),
            (19931, 1, 232, "primitive:uchar", 0),
            (19932, 4, 253, "primitive:int", 0),
            (19936, 4, 266, "primitive:int", 0),
            (19948, 4, 322, "primitive:int", 0),
            (19952, 4, 335, "primitive:int", 0),
            (19956, 4, 348, "primitive:int", 0),
        ),
    },
)
