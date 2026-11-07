# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Assembly.ComponentRead import KComponentBase
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Topology.BodyCollection import (
    KBodyCollection,
    KBodyComponent,
)

# the continuation prefix identifies the saved design collection among other component records
KCurrentLinks = (
    "0C5DAB90-715E-49EA-A56E-E30F2328F43E",
    "47C245A2-2DBE-4B1F-9C56-762F373BB0C8",
    "AC202226-A700-462A-BC41-13631C9E95D5",
    "596C8B98-D176-4E40-B294-6404BAD566BC",
    KBodyCollection,
)

# native undefined component coordinates separate two pairs of typed owned references
KUnsetBounds = bytes.fromhex("000000000000f0bf") * 4


# qualify the specific continuation slot before following any component body membership
def ReadCurrentLink(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    BaseSpan: RecordSpan,
    ComponentId: int,
) -> int:
    SelectCursor(BulkData, Owners, ComponentId, KBodyComponent)
    if (
        BaseSpan.IsPrimary
        or BaseSpan.ObjectId != ComponentId
        or BaseSpan.ClassGuid != KComponentBase
        or not 0 <= BaseSpan.PayloadOffset <= BaseSpan.EndOffset <= len(BulkData)
    ):
        raise ValueError("Invalid Fusion body component continuation")
    Cursor = MetaCursor(BulkData[BaseSpan.PayloadOffset : BaseSpan.EndOffset])
    if Cursor.TakeBytes(4) != bytes(4):
        raise ValueError("Unsupported Fusion body component continuation prefix")
    for FieldIndex, ClassGuid in enumerate(KCurrentLinks):
        if FieldIndex == 2 and Cursor.TakeBytes(32) != KUnsetBounds:
            raise ValueError("Unsupported Fusion body component reference framing")
        Identity = ReadNativeRef(Cursor)
        Linked = SelectCursor(BulkData, Owners, Identity, ClassGuid)
        Linked.Offset = len(Linked.DataValue) - 11
        if ReadNativeRef(Linked) != ComponentId:
            raise ValueError("Fusion body component reference owner disagrees")
    return Identity
