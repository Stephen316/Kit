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
                25992,
                16,
                "MoSketchBlockMgrCPersistentIdentifier",
                "direct:IHH8B",
                (598280617, 30861, 17766, 171, 95, 44, 90, 37, 103, 161, 250),
            ),
        ),
    },
)
