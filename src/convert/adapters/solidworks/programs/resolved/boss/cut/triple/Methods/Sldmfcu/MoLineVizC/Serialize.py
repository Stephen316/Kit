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
            (6228, 4, 166, "primitive:int", -1),
            (6232, 4, 245, "primitive:int", 1),
            (8275, 4, 166, "primitive:int", -1),
            (8279, 4, 245, "primitive:int", 1),
            (13470, 4, 166, "primitive:int", -1),
            (13474, 4, 245, "primitive:int", 1),
            (18631, 4, 166, "primitive:int", -1),
            (18635, 4, 245, "primitive:int", 1),
            (23701, 4, 166, "primitive:int", -1),
            (23705, 4, 245, "primitive:int", 1),
        ),
    },
)
