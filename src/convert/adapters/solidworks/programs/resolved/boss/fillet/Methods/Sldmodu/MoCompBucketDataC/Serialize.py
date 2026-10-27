# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompBucketDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (11857, 4, 1075, "primitive:long", 0),
            (11909, 4, 1203, "primitive:ulong", 0),
            (11913, 4, 1227, "primitive:long", 0),
            (13875, 4, 1075, "primitive:long", 0),
            (13927, 4, 1203, "primitive:ulong", 0),
            (13931, 4, 1227, "primitive:long", 0),
            (14516, 4, 1075, "primitive:long", 0),
            (14568, 4, 1203, "primitive:ulong", 0),
            (14572, 4, 1227, "primitive:long", 0),
            (14856, 4, 1075, "primitive:long", 0),
            (14908, 4, 1203, "primitive:ulong", 0),
            (14912, 4, 1227, "primitive:long", 0),
        ),
    },
)
