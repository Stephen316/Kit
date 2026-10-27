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
            (1039, 1, 4509, "primitive:uchar", 0),
            (1158, 1, 4509, "primitive:uchar", 0),
            (1277, 1, 4509, "primitive:uchar", 0),
            (1396, 1, 4509, "primitive:uchar", 0),
            (1515, 1, 4509, "primitive:uchar", 0),
            (6391, 1, 4509, "primitive:uchar", 0),
            (8591, 1, 4509, "primitive:uchar", 0),
            (13747, 1, 4509, "primitive:uchar", 0),
            (14167, 1, 4509, "primitive:uchar", 0),
            (18908, 1, 4509, "primitive:uchar", 0),
            (19296, 1, 4509, "primitive:uchar", 0),
            (23978, 1, 4509, "primitive:uchar", 0),
            (24366, 1, 4509, "primitive:uchar", 0),
        ),
    },
)
