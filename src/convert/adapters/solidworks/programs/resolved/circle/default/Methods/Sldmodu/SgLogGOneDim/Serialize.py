# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGOneDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7253, 2, 1930, "primitive:ushort", 0),
            (7255, 2, 1953, "primitive:ushort", 0),
            (7259, 2, 2380, "primitive:ushort", 0),
            (7261, 4, 2445, "primitive:long", -1),
            (7265, 4, 2467, "primitive:long", -1),
            (7269, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (7277, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (7291, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
