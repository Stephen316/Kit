# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (15577, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (15585, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (15593, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (15601, 4, 258, "primitive:int", 0),
            (15605, 4, 291, "primitive:int", 0),
            (15609, 4, 353, "primitive:int", 0),
            (15613, 4, 386, "primitive:int", 1),
            (15617, 4, 419, "primitive:int", 1),
        ),
    },
)
