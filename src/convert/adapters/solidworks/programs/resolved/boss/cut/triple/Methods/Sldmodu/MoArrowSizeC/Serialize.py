# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoArrowSizeC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (2845, 8, 12364, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2853, 8, 12380, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (2863, 4, 12686, "primitive:long", 0),
            (2867, 4, 12862, "primitive:long", 0),
        ),
    },
)
