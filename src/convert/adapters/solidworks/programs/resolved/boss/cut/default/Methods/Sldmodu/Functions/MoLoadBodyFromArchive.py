from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.Functions.MoLoadBodyFromArchive import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5870, 1, 119, "primitive:uchar", 1),
            (8090, 1, 119, "primitive:uchar", 1),
            (13246, 1, 119, "primitive:uchar", 1),
        ),
    },
)
