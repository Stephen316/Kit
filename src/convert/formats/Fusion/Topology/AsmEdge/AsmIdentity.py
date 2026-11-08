# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.Topology.AsmEdge.AsmFields import RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable

# the explicit identity record stores basis translation unit scale and inactive flags
KIdentityFields = (
    (12, -1),
    (4, -1),
    (20, (1.0, 0.0, 0.0)),
    (20, (0.0, 1.0, 0.0)),
    (20, (0.0, 0.0, 1.0)),
    (20, (0.0, 0.0, 0.0)),
    (6, 1.0),
    (11, None),
    (11, None),
    (11, None),
)


# identity placement preserves the component coordinates of the independent prism
def CheckAsmIdent(Table: AsmTable, TransformId: int) -> None:
    Value = RequireAsm(Table, TransformId, "transform", len(KIdentityFields))
    if Value.Tokens != KIdentityFields:
        raise ValueError("Fusion ASM prism placement is not identity")
