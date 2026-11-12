from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.MoTransRefPlaneDataCSecondInlineTransformRow import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (
                5002,
                16,
                "MoTransRefPlaneDataCSecondInlineTransformRow",
                "direct:2d",
                (float.fromhex("0x0.0p+0"), float.fromhex("0x0.0p+0")),
            ),
        ),
    },
)
