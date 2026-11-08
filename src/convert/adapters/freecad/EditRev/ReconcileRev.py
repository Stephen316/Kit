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
from convert.adapters.freecad.EditBinding import HasLegacyEdit, ReadEditBinding
from convert.adapters.freecad.EditRead.Revolve.ReadRevFields import ReadRevFields
from convert.adapters.freecad.EditRev.ApplyRevEdit import ApplyRevEdit
from convert.adapters.freecad.EditRev.RevBinding import KRevBinding
from convert.adapters.freecad.EditShape.Revolution.RevolveShape import (
    IsEditRevolve,
    KMaxRevolveBytes,
)
from convert.adapters.freecad.EditShape.SavedSketchWire import (
    IsSketchCache,
    KMaxSketchBytes,
)
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve


# only a saved solid and profile consistent with all native controls may replace the snapshot
def ReconcileRev(
    DocValue: CadDocument,
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KRevBinding)
    Feature = DocValue.feature_timeline[-1] if DocValue.feature_timeline else None
    IsAngular = Feature is not None and isinstance(Feature.definition, AngularRevolve)
    if Binding is None and not (IsAngular and HasLegacyEdit(RootValue)):
        return DocValue
    if Feature is None or (Binding is not None and Binding != Feature.id):
        raise ValueError("FreeCAD editable Revolve binding disagrees with its source")
    Plan = ReadEditRevolve(DocValue, Feature)
    if Plan is None:
        raise ValueError("FreeCAD editable Revolve binding has no qualified source")
    Fields = ReadRevFields(RootValue, DocValue, Plan)
    if any(
        Name not in Members or Members[Name].file_size for Name in Fields.EmptyEntries
    ):
        raise ValueError("FreeCAD editable Revolve has an additional or missing shape")
    if Fields.SketchEntry:
        SketchData = ReadEditBrep(
            Archive,
            Members,
            Fields.SketchEntry,
            KMaxSketchBytes,
            "editable Revolve sketch",
        )
        if not IsSketchCache(
            SketchData,
            Fields.ProfileSketch,
            DocValue.support_planes[0].transform,
            ClosedWire=True,
            AllowPcurves=True,
        ):
            raise ValueError(
                "FreeCAD editable Revolve sketch cache disagrees with its profile"
            )
    elif Fields.ProfileSketch != DocValue.sketches[0]:
        raise ValueError("FreeCAD editable Revolve profile has no saved sketch shape")
    Against = (
        (Fields.AgainstRad, Fields.AgainstText)
        if Fields.AgainstRad is not None and Fields.AgainstText is not None
        else None
    )
    Rebuilt = ApplyRevEdit(
        DocValue, Fields.ProfileSketch, (Fields.AlongRad, Fields.AlongText), Against
    )
    ShapeData = ReadEditBrep(
        Archive, Members, Fields.ShapeEntry, KMaxRevolveBytes, "editable Revolve"
    )
    if Rebuilt.brep is None or not IsEditRevolve(ShapeData, Rebuilt.brep):
        raise ValueError(
            "FreeCAD editable Revolve shape disagrees with its live controls"
        )
    return Rebuilt
