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
            (11854, 4, 1075, "primitive:long", 0),
            (11906, 4, 1203, "primitive:ulong", 0),
            (11910, 4, 1227, "primitive:long", 0),
            (15693, 4, 1075, "primitive:long", 0),
            (15745, 4, 1203, "primitive:ulong", 0),
            (15749, 4, 1227, "primitive:long", 0),
        ),
    },
)
