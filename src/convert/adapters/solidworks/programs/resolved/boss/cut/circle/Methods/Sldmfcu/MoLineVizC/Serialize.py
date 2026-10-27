# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLineVizC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5990, 4, 166, "primitive:int", -1),
            (5994, 4, 245, "primitive:int", 1),
            (8037, 4, 166, "primitive:int", -1),
            (8041, 4, 245, "primitive:int", 1),
            (13232, 4, 166, "primitive:int", -1),
            (13236, 4, 245, "primitive:int", 1),
            (17474, 4, 166, "primitive:int", -1),
            (17478, 4, 245, "primitive:int", 1),
        ),
    },
)
