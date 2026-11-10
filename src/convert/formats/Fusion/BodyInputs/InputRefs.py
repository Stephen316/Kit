# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.BodyInputs.BodyInput import BodyInput
from convert.formats.Fusion.BodyInputs.ProxyInputCheck import CheckInputProxy
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectList
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.formats.Fusion.Topology.BodyPick import KBodyDesc

# one feature can only address a bounded list of selections
KMaxBodyInputs = 1024


# typed counted slots keep input references distinct from adjacent output fields
def ReadPickRefs(
    Cursor: MetaCursor, Owners: dict[int, RecordSpan], ClassGuid: str
) -> tuple[int, ...]:
    References = tuple(
        ReadNativeRef(Cursor) for _ in range(Cursor.ReadCount(KMaxBodyInputs))
    )
    if len(set(References)) != len(References) or any(
        Identity not in Owners or Owners[Identity].ClassGuid != ClassGuid
        for Identity in References
    ):
        raise ValueError(
            "Fusion body input reference is repeated or has the wrong type"
        )
    return References


# optional empty attributes do not change the following feature role fields
def CheckPickPrefix(Cursor: MetaCursor) -> None:
    if Cursor.DataValue[:2] == b"\x00\x01":
        if ReadGeomAttrs(Cursor):
            raise ValueError("Unsupported Fusion body input feature attributes")
    elif Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion body input feature prefix")


# each operation can distinguish its plain selectors from operation owned selectors
def ReadInputPicks(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    ProxyId: int,
    RoleValue: str,
    ModeCode: int,
    Expected: dict[str, int] | None = None,
) -> tuple[BodyInput, ...]:
    Descriptors, Attributes = ReadSelectList(BulkData, Owners, ProxyId, FeatureId)
    if Attributes != (Expected or {}) or any(
        type(Value) is not int for Value in Attributes.values()
    ):
        raise ValueError("Fusion body input proxy attributes disagree with its role")
    if any(Owners[Identity].ClassGuid != KBodyDesc for Identity in Descriptors):
        raise ValueError("Fusion input proxy does not select whole bodies")
    CheckInputProxy(BulkData, Owners, ProxyId, Descriptors, ModeCode)
    return tuple(BodyInput(RoleValue, ProxyId, Identity) for Identity in Descriptors)
