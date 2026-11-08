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
from convert.adapters.freecad.ArchiveEditPlan import KProfileBinding, ReadArchiveEdit
from convert.adapters.freecad.EditableExt import EditExtrude, FindEditFrame
from convert.adapters.freecad.EditBinding import HasLegacyEdit, ReadEditBinding
from convert.adapters.freecad.EditExtProfile import GetEditCircle
from convert.adapters.freecad.EditRead.ReadControls import EditFields, ReadEditFields
from convert.adapters.freecad.EditShape.CylinderShape import (
    IsEditCylinder,
    KMaxCylinderBytes,
)
from convert.adapters.freecad.EditShape.SketchWire import IsSketchWire
from convert.adapters.freecad.EditShape.OpenSketch import IsOpenSketchCache
from convert.geometry.Formula.Arithmetic import EvalFormula, ReadFormula
from interchange.document.models.DocumentModel import CadDocument


# archive resource limits also apply to the native shape used as readback evidence
def ReadEditBrep(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    ShapeEntry: str,
    Limit: int = KMaxCylinderBytes,
    Purpose: str = "editable extrusion",
) -> bytes:
    EntryInfo = Members.get(ShapeEntry)
    if EntryInfo is None or not 0 < EntryInfo.file_size <= Limit:
        raise ValueError(f"FreeCAD {Purpose} has no readable shape entry")
    try:
        return Archive.read(EntryInfo)
    except (BadZipFile, OSError, RuntimeError, NotImplementedError) as ErrorInfo:
        raise ValueError(f"FreeCAD {Purpose} shape entry is corrupt") from ErrorInfo


# native unit normalization must not replace a source value for an unchanged literal
def IsSameEdit(
    DocValue: CadDocument, PlanValue: EditExtrude, Fields: EditFields
) -> bool:
    if PlanValue.HasFormula:
        return not Fields.ParameterEdits
    if Fields.DistanceMm == PlanValue.DistanceMm:
        return True
    Expression = DocValue.parameter(PlanValue.ParameterId).expression
    Before = None if Expression is None else ReadFormula(Expression.source)
    After = ReadFormula(Fields.SourceText)
    if Before is None or After is None:
        return False
    Original = EvalFormula(Before, {})
    return Original is not None and Original == EvalFormula(After, {})


# only corroborated native depth edits can override the reversible source snapshot
def ReconcileEdit(
    DocValue: CadDocument,
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue)
    ProfileBinding = ReadEditBinding(RootValue, KProfileBinding)
    EditPlan = ReadArchiveEdit(DocValue)
    if Binding is not None and (EditPlan is None or Binding != EditPlan[0]):
        raise ValueError("FreeCAD editable extrusion binding disagrees with its source")
    if ProfileBinding is not None and (
        Binding is None
        or EditPlan is None
        or not EditPlan[1].ProfileEditable
        or ProfileBinding != EditPlan[1].SketchId
    ):
        raise ValueError("FreeCAD editable profile binding disagrees with its source")
    if EditPlan is None:
        return DocValue
    _, Plan = EditPlan
    Fields = ReadEditFields(
        RootValue, DocValue, Plan, AllowProfile=ProfileBinding is not None
    )
    if Fields is None:
        if Binding is not None or HasLegacyEdit(RootValue):
            raise ValueError("FreeCAD editable extrusion feature is missing")
        return DocValue
    if any(Members[EntryName].file_size for EntryName in Fields.EmptyEntries):
        raise ValueError("FreeCAD editable extrusion has an additional nonempty shape")
    ProfileFrame = FindEditFrame(DocValue, Plan.SketchId)
    if ProfileFrame is None:
        raise ValueError("FreeCAD editable extrusion source sketch is unavailable")
    SketchValue, PlaneValue = ProfileFrame
    Profile = GetEditCircle(DocValue.feature_timeline[-1], Fields.ProfileSketch)
    FrameValue = PlaneValue.transform
    if Profile is None:
        raise ValueError("FreeCAD editable extrusion source profile is unavailable")
    EditedSketch = (
        Fields.ProfileSketch if Fields.ProfileSketch is not SketchValue else None
    )
    if Fields.SketchEntry and Members[Fields.SketchEntry].file_size:
        if not IsSketchWire(
            ReadEditBrep(Archive, Members, Fields.SketchEntry), FrameValue, Profile
        ):
            raise ValueError("FreeCAD editable sketch cache disagrees with its profile")
    elif EditedSketch is not None:
        raise ValueError("FreeCAD editable profile has no saved sketch shape")
    for CacheValue in Fields.IndependentCaches:
        if Members[CacheValue.EntryName].file_size and not IsOpenSketchCache(
            ReadEditBrep(Archive, Members, CacheValue.EntryName),
            CacheValue.SketchValue,
            CacheValue.FrameValue,
        ):
            raise ValueError(
                "FreeCAD unrelated sketch cache disagrees with its geometry"
            )
    ShapeData = ReadEditBrep(Archive, Members, Fields.ShapeEntry)
    if not IsEditCylinder(ShapeData, FrameValue, Profile, Fields.DistanceMm):
        raise ValueError(
            "FreeCAD editable extrusion shape disagrees with its live controls"
        )
    SameDepth = IsSameEdit(DocValue, Plan, Fields)
    if SameDepth and EditedSketch is None:
        return DocValue
    return ApplyDepthEdit(
        DocValue,
        Plan.ParameterId,
        None if SameDepth else Fields.SourceText,
        Fields.DistanceMm,
        Profile,
        FrameValue,
        Fields.ParameterEdits,
        EditedSketch=EditedSketch,
    )
