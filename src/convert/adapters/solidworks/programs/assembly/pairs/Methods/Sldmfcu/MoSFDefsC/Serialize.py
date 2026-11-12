from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSFDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10451, 4, 167, "primitive:int", 0),
            (10455, 4, 188, "primitive:int", 2),
            (10459, 8, 208, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
            (10467, 8, 221, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
        ),
    },
)
