# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.MoRelMgrCStatusNameTable import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (
                3615,
                126,
                "MoRelMgrCStatusNameTable",
                "stringlist",
                (
                    "Description",
                    "High Priority",
                    "Low Priority",
                    "Complete",
                    "Reminder",
                ),
            ),
        ),
    },
)
