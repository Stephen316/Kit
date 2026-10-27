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
            (2895, 4, 100, "primitive:long", 0),
            (2899, 4, 100, "primitive:long", 0),
            (2913, 4, 100, "primitive:long", 0),
            (2939, 4, 100, "primitive:long", 0),
            (3414, 4, 100, "primitive:long", 0),
            (3418, 4, 100, "primitive:long", 0),
            (3432, 4, 100, "primitive:long", 0),
            (3458, 4, 100, "primitive:long", 0),
            (3984, 4, 100, "primitive:long", 0),
            (3988, 4, 100, "primitive:long", 0),
            (4002, 4, 100, "primitive:long", 0),
            (4028, 4, 100, "primitive:long", 0),
        ),
    },
)
