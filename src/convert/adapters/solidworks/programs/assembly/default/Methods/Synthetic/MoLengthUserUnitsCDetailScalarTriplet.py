from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.MoLengthUserUnitsCDetailScalarTriplet import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (
                17610,
                12,
                "MoLengthUserUnitsCDetailScalarTriplet",
                "direct:3i",
                (0, 0, 0),
            ),
        ),
    },
)
