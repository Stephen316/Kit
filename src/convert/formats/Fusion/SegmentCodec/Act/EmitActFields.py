# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SegmentCodec.Act.CheckActKey import CheckActKey
from convert.formats.Fusion.SegmentCodec.Act.EmitActTokens import EmitActRolesMut
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# a generated fields record ends at its reciprocal key without unexplained source data
def EmitActFields(KeyValue: str, Roles: tuple[tuple[ActRole, str], ...]) -> bytes:
    CheckActKey(KeyValue)
    SinkValue = MetaSink()
    SinkValue.AddBytes(bytes(6))
    EmitActRolesMut(SinkValue, Roles)
    SinkValue.AddText(KeyValue, WideText=True)
    return bytes(SinkValue.Buffer)
