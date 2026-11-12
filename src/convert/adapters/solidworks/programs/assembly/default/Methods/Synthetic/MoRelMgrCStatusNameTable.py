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
        "Contents/Config-0": (
            (
                3477,
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
