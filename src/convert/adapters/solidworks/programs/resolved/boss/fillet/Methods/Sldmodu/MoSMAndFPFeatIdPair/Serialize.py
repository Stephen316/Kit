# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoSMAndFPFeatIdPair.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (682, 1, 4509, "primitive:uchar", 0),
            (801, 1, 4509, "primitive:uchar", 0),
            (920, 1, 4509, "primitive:uchar", 0),
            (5796, 1, 4509, "primitive:uchar", 0),
            (7996, 1, 4509, "primitive:uchar", 0),
            (11771, 1, 4509, "primitive:uchar", 0),
            (13789, 1, 4509, "primitive:uchar", 0),
            (14028, 1, 4509, "primitive:uchar", 0),
            (14288, 1, 4509, "primitive:uchar", 0),
            (14628, 1, 4509, "primitive:uchar", 0),
        ),
    },
)
