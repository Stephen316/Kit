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
            (18151, 1, 188, "primitive:uchar", 0),
            (18152, 1, 210, "primitive:uchar", 0),
            (18153, 1, 232, "primitive:uchar", 0),
            (18154, 4, 253, "primitive:int", 0),
            (18158, 4, 266, "primitive:int", 0),
            (18170, 4, 322, "primitive:int", 0),
            (18174, 4, 335, "primitive:int", 0),
            (18178, 4, 348, "primitive:int", 0),
        ),
    },
)
