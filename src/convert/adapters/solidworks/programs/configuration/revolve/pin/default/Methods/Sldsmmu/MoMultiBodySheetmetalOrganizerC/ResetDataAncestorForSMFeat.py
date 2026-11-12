from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldsmmu.MoMultiBodySheetmetalOrganizerC.ResetDataAncestorForSMFeat import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": ((24878, 4, 5202, "primitive:long", 0),),
    },
)
