# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5808, 4, 37887, "primitive:long", 0),
            (5812, 4, 37887, "primitive:long", 0),
            (5816, 4, 37887, "primitive:long", 0),
            (5820, 4, 37887, "primitive:long", 0),
            (7855, 4, 37887, "primitive:long", 0),
            (7859, 4, 37887, "primitive:long", 0),
            (7863, 4, 37887, "primitive:long", 0),
            (7867, 4, 37887, "primitive:long", 0),
            (14180, 4, 37887, "primitive:long", 0),
            (14184, 4, 37887, "primitive:long", 0),
            (14188, 4, 37887, "primitive:long", 0),
            (14192, 4, 37887, "primitive:long", 0),
        ),
    },
)
