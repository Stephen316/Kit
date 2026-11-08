# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AnglePlane.AnglePlaneSource import AttachAngleDef
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.NativePlane import KPlaneFeature, ReadNativePlane
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic


# selected history limits geometry to the component being projected
def ProjectPlanes(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> tuple[tuple[SupportPlane, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Planes: list[SupportPlane] = []
    Diagnostics: list[Diagnostic] = []
    for Identity in History.EntryIds:
        Feature = Owners[Identity]
        if Feature.ClassGuid != KPlaneFeature:
            continue
        try:
            PlaneValue = ReadNativePlane(BulkData, Feature, Owners)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.plane.unsupported",
                    message=str(ErrorInfo),
                    provenance=RecordOrigin(Feature),
                )
            )
            continue
        try:
            Qualified = AttachAngleDef(BulkData, Owners, PlaneValue)
        except ValueError:
            Qualified = PlaneValue
        Planes.append(Qualified)
    return tuple(Planes), tuple(Diagnostics)
