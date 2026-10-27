# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Slduiu.UiModelMapC.OnViewAllComments import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Definition": (
            (3595, 4, 1535, "primitive:long", 0),
            (3601, 4, 2562, "primitive:long", 1),
            (3607, 4, 3299, "primitive:long", 1),
        ),
    },
)
