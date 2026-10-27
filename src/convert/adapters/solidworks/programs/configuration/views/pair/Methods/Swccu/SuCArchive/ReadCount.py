# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadCount import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (564, 2, 19, "primitive:ushort", 0),
            (566, 2, 19, "primitive:ushort", 0),
            (568, 2, 19, "primitive:ushort", 0),
            (570, 2, 19, "primitive:ushort", 0),
            (572, 2, 19, "primitive:ushort", 0),
            (574, 2, 19, "primitive:ushort", 0),
            (576, 2, 19, "primitive:ushort", 0),
            (578, 2, 19, "primitive:ushort", 0),
            (582, 2, 19, "primitive:ushort", 0),
        ),
    },
)
