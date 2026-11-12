from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCSysRefPlnDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (17811, 8, 6660, "primitive:double", float.fromhex("0x0.0p+0")),
            (17819, 8, 6676, "primitive:double", float.fromhex("0x1.47ae147ae147bp-8")),
        ),
    },
)
