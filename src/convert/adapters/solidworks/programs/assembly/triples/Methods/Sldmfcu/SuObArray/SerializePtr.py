# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.SuObArray.SerializePtr import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (2951, 4, 100, "primitive:long", 0),
            (2955, 4, 100, "primitive:long", 0),
            (2969, 4, 100, "primitive:long", 0),
            (2995, 4, 100, "primitive:long", 0),
            (3470, 4, 100, "primitive:long", 0),
            (3474, 4, 100, "primitive:long", 0),
            (3488, 4, 100, "primitive:long", 0),
            (3514, 4, 100, "primitive:long", 0),
            (4040, 4, 100, "primitive:long", 0),
            (4044, 4, 100, "primitive:long", 0),
            (4058, 4, 100, "primitive:long", 0),
            (4084, 4, 100, "primitive:long", 0),
        ),
    },
)
