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
            (3119, 4, 100, "primitive:long", 0),
            (3123, 4, 100, "primitive:long", 0),
            (3137, 4, 100, "primitive:long", 0),
            (3163, 4, 100, "primitive:long", 0),
            (3638, 4, 100, "primitive:long", 0),
            (3642, 4, 100, "primitive:long", 0),
            (3656, 4, 100, "primitive:long", 0),
            (3682, 4, 100, "primitive:long", 0),
            (4208, 4, 100, "primitive:long", 0),
            (4212, 4, 100, "primitive:long", 0),
            (4226, 4, 100, "primitive:long", 0),
            (4252, 4, 100, "primitive:long", 0),
        ),
    },
)
