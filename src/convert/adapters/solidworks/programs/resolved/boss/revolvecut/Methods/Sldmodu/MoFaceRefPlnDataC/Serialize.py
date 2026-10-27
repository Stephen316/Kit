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
            (9115, 4, 7121, "primitive:long", 1),
            (9143, 8, 7292, "primitive:double", float.fromhex("0x1.776793ed35a44p-5")),
            (15417, 4, 7121, "primitive:long", 1),
            (15445, 8, 7292, "primitive:double", float.fromhex("0x1.776793ed35a45p-5")),
            (15830, 8, 5803, "primitive:double", float.fromhex("0x0.0p+0")),
            (15838, 1, 5864, "primitive:uchar", 0),
        ),
    },
)
