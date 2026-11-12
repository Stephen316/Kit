from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.MoTransRefPlaneDataCFirstInlineTransformRow import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (
                2540,
                16,
                "MoTransRefPlaneDataCFirstInlineTransformRow",
                "direct:2d",
                (float.fromhex("0x0.0p+0"), float.fromhex("0x0.0p+0")),
            ),
        ),
    },
)
