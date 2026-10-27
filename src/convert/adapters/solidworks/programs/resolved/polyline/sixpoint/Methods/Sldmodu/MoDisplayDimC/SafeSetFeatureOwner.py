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
            (5620, 4, 4724, "primitive:ulong", 0),
            (5624, 4, 4744, "primitive:long", 0),
            (5628, 4, 1931, "primitive:long", 3),
            (5633, 4, 2342, "primitive:long", 0),
            (5643, 4, 3319, "primitive:ulong", 100000),
            (8863, 4, 4724, "primitive:ulong", 1),
            (8867, 4, 4744, "primitive:long", 1),
            (8978, 4, 1931, "primitive:long", 3),
            (8983, 4, 2342, "primitive:long", 0),
            (8993, 4, 3319, "primitive:ulong", 100000),
        ),
    },
)
