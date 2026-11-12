from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.ModelHeaderUserAndLogPreamble import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ModelHeader": (
            (
                41,
                14,
                "ModelHeaderUserAndLogPreamble",
                "direct:7H",
                (1, 65279, 1279, 111, 100, 105, 110),
            ),
        ),
    },
)
