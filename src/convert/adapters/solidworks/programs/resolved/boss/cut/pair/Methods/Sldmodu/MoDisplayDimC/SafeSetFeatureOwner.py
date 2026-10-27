# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoDisplayDimC.SafeSetFeatureOwner import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6096, 4, 4724, "primitive:ulong", 0),
            (6100, 4, 4744, "primitive:long", 0),
            (6104, 4, 1931, "primitive:long", 3),
            (6109, 4, 2342, "primitive:long", 0),
            (6119, 4, 3319, "primitive:ulong", 100000),
            (8217, 4, 4724, "primitive:ulong", 1),
            (8221, 4, 4744, "primitive:long", 1),
            (8324, 4, 1931, "primitive:long", 3),
            (8329, 4, 2342, "primitive:long", 0),
            (8339, 4, 3319, "primitive:ulong", 100000),
            (13392, 4, 4724, "primitive:ulong", 1),
            (13396, 4, 4744, "primitive:long", 1),
            (13480, 4, 1931, "primitive:long", 3),
            (13485, 4, 2342, "primitive:long", 0),
            (13495, 4, 3319, "primitive:ulong", 100000),
            (18553, 4, 4724, "primitive:ulong", 1),
            (18557, 4, 4744, "primitive:long", 1),
            (18641, 4, 1931, "primitive:long", 3),
            (18646, 4, 2342, "primitive:long", 0),
            (18656, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
