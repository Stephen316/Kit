# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.LoadSketchInPlace import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5836, 4, 3276, "primitive:long", 1),
            (6753, 4, 3276, "primitive:long", 4),
            (11964, 4, 3276, "primitive:long", 4),
            (17125, 4, 3276, "primitive:long", 4),
            (22195, 4, 3276, "primitive:long", 4),
        ),
    },
)
