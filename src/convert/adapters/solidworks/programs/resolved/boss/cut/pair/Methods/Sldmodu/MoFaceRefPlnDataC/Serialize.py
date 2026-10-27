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
            (9353, 4, 7121, "primitive:long", 1),
            (9381, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
            (14677, 4, 7121, "primitive:long", 1),
            (14705, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
            (19747, 4, 7121, "primitive:long", 1),
            (19775, 8, 7292, "primitive:double", float.fromhex("0x1.f32cae0a1dfa5p-5")),
        ),
    },
)
