from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.DisplayDimensionDerivedScalars import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (
                10702,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-7"),
            ),
            (
                16011,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-8"),
            ),
        ),
    },
)
