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
                9401,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-6"),
            ),
            (
                10866,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.eb851eb851eb8p-7"),
            ),
            (
                14268,
                8,
                "DisplayDimensionThreeDerivedScalar",
                "direct:d",
                float.fromhex("0x1.89374bc6a7efap-7"),
            ),
        ),
    },
)
