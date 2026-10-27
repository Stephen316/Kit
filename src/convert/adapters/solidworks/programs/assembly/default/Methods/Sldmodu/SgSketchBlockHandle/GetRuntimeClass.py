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
        "Contents/Config-0": (
            (24092, 4, 3099, "primitive:long", 0),
            (24098, 4, 3154, "primitive:long", 0),
            (24102, 4, 4083, "primitive:ulong", 0),
        ),
        "Contents/Config-0-ResolvedFeatures": (
            (5004, 4, 15839, "primitive:long", 0),
            (5008, 4, 16002, "primitive:long", 0),
            (5012, 4, 16657, "primitive:long", 0),
        ),
    },
)
