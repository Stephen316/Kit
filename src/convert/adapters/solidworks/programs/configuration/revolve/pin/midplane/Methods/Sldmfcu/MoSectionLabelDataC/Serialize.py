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
        "Configuration": (
            (13799, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (13807, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (13815, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (13823, 4, 258, "primitive:int", 0),
            (13827, 4, 291, "primitive:int", 0),
            (13831, 4, 353, "primitive:int", 0),
            (13835, 4, 386, "primitive:int", 1),
            (13839, 4, 419, "primitive:int", 1),
        ),
    },
)
