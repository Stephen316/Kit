# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6346, 1, 119, "primitive:uchar", 1),
            (8566, 1, 119, "primitive:uchar", 1),
            (13722, 1, 119, "primitive:uchar", 1),
            (18883, 1, 119, "primitive:uchar", 1),
            (23953, 1, 119, "primitive:uchar", 1),
        ),
    },
)
