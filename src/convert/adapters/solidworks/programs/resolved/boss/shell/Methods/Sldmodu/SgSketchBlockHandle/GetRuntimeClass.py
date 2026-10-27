# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5711, 4, 15839, "primitive:long", 0),
            (5715, 4, 16002, "primitive:long", 0),
            (5719, 4, 16657, "primitive:long", 0),
            (7832, 4, 15839, "primitive:long", 0),
            (7836, 4, 16002, "primitive:long", 0),
            (7840, 4, 16657, "primitive:long", 0),
        ),
    },
)
