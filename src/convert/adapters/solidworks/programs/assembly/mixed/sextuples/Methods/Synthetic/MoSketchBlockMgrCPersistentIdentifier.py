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
                25854,
                16,
                "MoSketchBlockMgrCPersistentIdentifier",
                "direct:IHH8B",
                (2600585247, 56037, 16416, 157, 174, 99, 41, 164, 37, 196, 103),
            ),
        ),
    },
)
