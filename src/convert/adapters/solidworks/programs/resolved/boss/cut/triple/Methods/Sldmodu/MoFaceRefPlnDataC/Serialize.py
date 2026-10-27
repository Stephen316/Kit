# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoFaceRefPlnDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9591, 4, 7121, "primitive:long", 1),
            (9619, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (14915, 4, 7121, "primitive:long", 1),
            (14943, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (19985, 4, 7121, "primitive:long", 1),
            (20013, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
            (25059, 4, 7121, "primitive:long", 1),
            (25087, 8, 7292, "primitive:double", float.fromhex("0x1.1b11a14904e08p-4")),
        ),
    },
)
