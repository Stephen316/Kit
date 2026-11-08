# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.AnglePlane.AnglePlaneSource import ReadAngleDef
from convert.formats.Fusion.Extrudes.Plane.OffsetBackend import CheckOffsetDef
from convert.formats.Fusion.Extrudes.Plane.OffsetOrigin import ReadOffsetOrg
from convert.formats.Fusion.PlaneCollection import ReadPlaneComp
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform


# source controls preserve the authored frame and native parameter identities independently
@MakeDataClass(frozen=True, slots=True)
class PlaneControls:
    Method: str
    ReferenceFrame: Transform
    ScalarBindingId: int
    OffsetBindingId: int
    ComponentId: int


# each method must reproduce the stored datum using its same component origin operands
def ReadPlaneControls(
    BulkData: bytes, Owners: dict[int, RecordSpan], PlaneValue: SupportPlane
) -> PlaneControls:
    Origin = PlaneValue.provenance
    Mode = PlaneValue.attributes.get("fusion.cached_plane_mode")
    FeatureId = PlaneValue.attributes.get("fusion.feature_object_id")
    if Origin is None or type(FeatureId) is not int or Mode not in (1, 2):
        raise ValueError("Fusion construction plane controls are unresolved")
    if Mode == 2:
        _, ReferenceFrame, Scalar, Extra, Component = ReadAngleDef(
            BulkData, Owners, PlaneValue
        )
        return PlaneControls("angle", ReferenceFrame, Scalar, Extra, Component)
    Component, _ = ReadPlaneComp(BulkData, Owners, PlaneValue)
    _, Extra, Scalar, _, _, BaseId, _ = CheckOffsetDef(
        BulkData,
        Owners,
        int(Origin.native_id),
        FeatureId,
        Component,
        PlaneValue.transform,
    )
    ReferenceFrame, _ = ReadOffsetOrg(BulkData, Owners, BaseId, Component)
    return PlaneControls("offset", ReferenceFrame, Scalar, Extra, Component)
