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
            (492, 2, 19, "primitive:ushort", 0),
            (494, 2, 19, "primitive:ushort", 0),
            (496, 2, 19, "primitive:ushort", 0),
            (498, 2, 19, "primitive:ushort", 0),
            (500, 2, 19, "primitive:ushort", 0),
            (502, 2, 19, "primitive:ushort", 0),
            (504, 2, 19, "primitive:ushort", 0),
            (506, 2, 19, "primitive:ushort", 0),
            (510, 2, 19, "primitive:ushort", 0),
        ),
    },
)
