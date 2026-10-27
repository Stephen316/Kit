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
            (6108, 1, 119, "primitive:uchar", 1),
            (8328, 1, 119, "primitive:uchar", 1),
            (13484, 1, 119, "primitive:uchar", 1),
            (17678, 1, 119, "primitive:uchar", 1),
        ),
    },
)
