# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoRefSurfaceC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (12433, 4, 5377, "primitive:long", 1),
            (12439, 4, 5575, "primitive:long", 0),
            (12461, 8, 5715, "primitive:double", float.fromhex("0x0.0p+0")),
            (12469, 4, 6052, "primitive:long", 0),
        ),
    },
)
