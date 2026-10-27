# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.MoSketchBlockMgrCPersistentIdentifier import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (
                24076,
                16,
                "MoSketchBlockMgrCPersistentIdentifier",
                "direct:IHH8B",
                (3151282961, 131, 20144, 185, 60, 121, 75, 230, 239, 118, 110),
            ),
        ),
    },
)
