# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import BadZipFile, ZipFile, ZipInfo

from convert.adapters.freecad.ApplyDepthEdit import ApplyDepthEdit
from convert.adapters.freecad.ArchiveEditPlan import ReadArchiveEdit
from convert.adapters.freecad.EditBinding import HasLegacyEdit, ReadEditBinding
from convert.adapters.freecad.EditExtProfile import GetEditCircle
from convert.adapters.freecad.EditRead.ReadControls import ReadEditFields
from convert.adapters.freecad.EditShape.CylinderShape import (
    IsEditCylinder,
    KMaxCylinderBytes,
)
from convert.adapters.freecad.EditShape.SketchWire import IsSketchWire
from interchange.document.models.DocumentModel import CadDocument


# archive resource limits also apply to the native shape used as readback evidence
def ReadEditBrep(
    Archive: ZipFile, Members: Mapping[str, ZipInfo], ShapeEntry: str
) -> bytes:
    EntryInfo = Members.get(ShapeEntry)
    if EntryInfo is None or not 0 < EntryInfo.file_size <= KMaxCylinderBytes:
        raise ValueError("FreeCAD editable extrusion has no readable shape entry")
    try:
        return Archive.read(EntryInfo)
    except (BadZipFile, OSError, RuntimeError, NotImplementedError) as ErrorInfo:
        raise ValueError(
            "FreeCAD editable extrusion shape entry is corrupt"
        ) from ErrorInfo


# only corroborated native depth edits can override the reversible source snapshot
def ReconcileEdit(
    DocValue: CadDocument,
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue)
    EditPlan = ReadArchiveEdit(DocValue)
    if Binding is not None and (EditPlan is None or Binding != EditPlan[0]):
        raise ValueError("FreeCAD editable extrusion binding disagrees with its source")
    if EditPlan is None:
        return DocValue
    _, Plan = EditPlan
    Fields = ReadEditFields(RootValue, DocValue, Plan)
    if Fields is None:
        if Binding is not None or HasLegacyEdit(RootValue):
            raise ValueError("FreeCAD editable extrusion feature is missing")
        return DocValue
    if any(Members[EntryName].file_size for EntryName in Fields.EmptyEntries):
        raise ValueError("FreeCAD editable extrusion has an additional nonempty shape")
    Profile = GetEditCircle(DocValue.feature_timeline[-1], DocValue.sketches[0])
    FrameValue = DocValue.support_planes[0].transform
    if Profile is None:
        raise ValueError("FreeCAD editable extrusion source profile is unavailable")
    if (
        Fields.SketchEntry
        and Members[Fields.SketchEntry].file_size
        and not IsSketchWire(
            ReadEditBrep(Archive, Members, Fields.SketchEntry), FrameValue, Profile
        )
    ):
        raise ValueError("FreeCAD editable sketch cache disagrees with its profile")
    ShapeData = ReadEditBrep(Archive, Members, Fields.ShapeEntry)
    if not IsEditCylinder(ShapeData, FrameValue, Profile, Fields.DistanceMm):
        raise ValueError(
            "FreeCAD editable extrusion shape disagrees with its live controls"
        )
    if Fields.DistanceMm == Plan.DistanceMm:
        return DocValue
    return ApplyDepthEdit(
        DocValue,
        Plan.ParameterId,
        Fields.SourceText,
        Fields.DistanceMm,
        Profile,
        FrameValue,
    )
