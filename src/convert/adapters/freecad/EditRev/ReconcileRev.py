# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditableRev import ReadEditRevolve
from convert.adapters.freecad.EditAxisRev.AxisRevBinding import KAxisRevBinding
from convert.adapters.freecad.EditAxisRev.ReconcileAxis import ReconcileAxis
from convert.adapters.freecad.EditBodyRev.BodyRevBinding import KBodyRevBinding
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import ReadBodyRev
from convert.adapters.freecad.EditBinding import HasLegacyEdit, ReadEditBinding
from convert.adapters.freecad.EditRead.Revolve.ReadRevFields import ReadRevFields
from convert.adapters.freecad.EditRev.ApplyRevEdit import ApplyRevEdit
from convert.adapters.freecad.EditRev.RevBinding import KRevBinding
from convert.adapters.freecad.EditRev.RevCacheProof import CheckRevSolid, CheckRevWire
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve


# only a saved solid and profile consistent with all native controls may replace the snapshot
def ReconcileRev(
    DocValue: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KRevBinding)
    AxisBinding = ReadEditBinding(RootValue, KAxisRevBinding)
    BodyBinding = ReadEditBinding(RootValue, KBodyRevBinding)
    Feature = DocValue.feature_timeline[-1] if DocValue.feature_timeline else None
    if BodyBinding is not None:
        if (
            Binding is not None
            or AxisBinding is not None
            or Feature is None
            or BodyBinding != Feature.id
            or ReadBodyRev(DocValue, Feature) is None
        ):
            raise ValueError(
                "FreeCAD editable body axis binding disagrees with its source"
            )
        return DocValue
    if AxisBinding is not None:
        if Binding is not None:
            raise ValueError(
                "FreeCAD editable sketch axis binding disagrees with its source"
            )
        return ReconcileAxis(
            DocValue, Manifest, RootValue, Archive, Members, AxisBinding
        )
    IsAngular = Feature is not None and isinstance(Feature.definition, AngularRevolve)
    if Binding is None and not (IsAngular and HasLegacyEdit(RootValue)):
        return DocValue
    if Feature is None or (Binding is not None and Binding != Feature.id):
        raise ValueError("FreeCAD editable Revolve binding disagrees with its source")
    Plan = ReadEditRevolve(DocValue, Feature)
    if Plan is None:
        raise ValueError("FreeCAD editable Revolve binding has no qualified source")
    Fields = ReadRevFields(RootValue, DocValue, Plan)
    CheckRevWire(
        Archive,
        Members,
        Fields.SketchEntry,
        Fields.EmptyEntries,
        DocValue.sketches[0],
        Fields.ProfileSketch,
        DocValue.support_planes[0].transform,
    )
    Against = (
        (Fields.AgainstRad, Fields.AgainstText)
        if Fields.AgainstRad is not None and Fields.AgainstText is not None
        else None
    )
    Rebuilt = ApplyRevEdit(
        DocValue, Fields.ProfileSketch, (Fields.AlongRad, Fields.AlongText), Against
    )
    CheckRevSolid(Archive, Members, Fields.ShapeEntry, Rebuilt)
    return Rebuilt
