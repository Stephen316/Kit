# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVisualOverlayObjectC.GetThisClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (765, 4, 2847, "primitive:long", 0),
            (777, 4, 2847, "primitive:long", 0),
            (781, 4, 3167, "primitive:long", 0),
            (817, 4, 4159, "primitive:long", 0),
            (825, 4, 2847, "primitive:long", 0),
            (2268, 4, 4159, "primitive:long", 0),
        ),
        "Contents/Config-0": (
            (18, 4, 6976, "primitive:long", 3406),
            (3428, 4, 6976, "primitive:long", 21639),
        ),
    },
)
