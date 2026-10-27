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
                24670,
                16,
                "MoSketchBlockMgrCPersistentIdentifier",
                "direct:IHH8B",
                (1223298575, 14418, 16519, 162, 97, 191, 112, 147, 201, 92, 133),
            ),
        ),
    },
)
