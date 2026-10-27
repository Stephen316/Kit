# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
                10690,
                8,
                "DisplayDimensionOneDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-8"),
            ),
            (
                13360,
                8,
                "DisplayDimensionTwoDerivedScalar",
                "direct:d",
                float.fromhex("0x1.8000000000000p+1"),
            ),
            (
                15047,
                8,
                "DisplayDimensionThreeDerivedScalar",
                "direct:d",
                float.fromhex("0x1.47ae147ae147bp-8"),
            ),
            (
                16598,
                8,
                "DisplayDimensionFourDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
            (
                18127,
                8,
                "DisplayDimensionFiveDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
            (
                20218,
                8,
                "DisplayDimensionSixDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
            (
                21801,
                8,
                "DisplayDimensionSevenDerivedScalar",
                "direct:d",
                float.fromhex("0x0.0p+0"),
            ),
        ),
    },
)
