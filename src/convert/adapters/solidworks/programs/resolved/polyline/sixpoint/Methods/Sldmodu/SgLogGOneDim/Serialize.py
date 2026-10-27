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
            (8505, 2, 1930, "primitive:ushort", 0),
            (8507, 2, 1953, "primitive:ushort", 0),
            (8511, 2, 2380, "primitive:ushort", 0),
            (8513, 4, 2445, "primitive:long", -1),
            (8517, 4, 2467, "primitive:long", -1),
            (8521, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (8529, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (8543, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
