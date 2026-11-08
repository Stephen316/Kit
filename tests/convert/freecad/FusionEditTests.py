# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import pi as HalfTurn
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import xml.etree.ElementTree as XmlTree
from zipfile import ZipFile

import pytest as Pytest

from convert import ApplicationUsabilityError as AppUsabilityError
from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.adapters.base.TransferContract import TransferMode
from interchange.enums.EnumDocument import Capability

# saved native controls exercise both the source parser and the target writer
KStudyPath = FilePath(__file__).parents[3] / "re" / "Fusion" / "Study"


# the installed application verifies geometry and editability independently of kit
KOraclePath = GetFreecadPath()


# the native edit must change the displayed solid through its spreadsheet dependency
KEditProbe = """
import os
import FreeCAD as App

doc = App.open(os.environ['KIT_ORACLE_PATH'])
(extrusion,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Extrusion']
assert extrusion.Base.TypeId == 'Sketcher::SketchObject'
params = doc.getObject('Parameters')
cell = params.getCellFromAlias('fusion_parameter_242')
for depth in (None, os.environ['KIT_ORACLE_DEPTH']):
    if depth is not None:
        params.set(cell, depth)
    doc.recompute()
    shape = extrusion.Shape
    visible = [obj for obj in doc.Objects if obj.isDerivedFrom('Part::Feature')
               and getattr(obj, 'Visibility', True) and obj.Shape.Solids]
    assert visible == [extrusion] and shape.isValid() and len(shape.Solids) == 1
    print('KIT_FUSION_EDIT', shape.Volume, shape.Area, shape.Solids[0].CenterOfMass.z)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
"""


# feature properties must belong to the one native extrusion that owns the visible solid
@Pytest.mark.parametrize(
    ("Folder", "SampleName", "DepthMm"),
    (
        ("extents-f0f33a9a605f", "distance_positive", 17.0),
        ("extents-f0f33a9a605f", "distance_negative", -17.0),
        ("holdouts-f8c508a73323", "independent_depth", 17.375),
        ("models-b8a640dbddc6", "new_body", 17.0),
    ),
)
def TestNativeExt(
    TmpPath: FilePath, Folder: str, SampleName: str, DepthMm: float
) -> None:
    Source = KStudyPath / Folder / f"{SampleName}.f3d"
    Document = OpenDocument(Source, strict=False)
    Output = TmpPath / f"{SampleName}.FCStd"
    Result = WriteDocument(Document, Output)
    Transfers = {Value.capability: Value.mode for Value in Result.transfers}
    assert Result.application_usable and Result.vendor_loadable
    assert Transfers[Capability.BREP] is TransferMode.NATIVE
    assert Transfers[Capability.PARAMETRIC_HISTORY] is TransferMode.MIXED
    assert Transfers[Capability.EXPRESSIONS] is TransferMode.NATIVE
    with ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Objects = {
            Value.attrib["name"]: Value.attrib["type"]
            for Value in RootValue.findall("./Objects/Object")
        }
        (Extrusion,) = (
            NameValue
            for NameValue, TypeValue in Objects.items()
            if TypeValue == "Part::Extrusion"
        )
        Properties = f"./ObjectData/Object[@name='{Extrusion}']/Properties"
        BaseLink = RootValue.find(f"{Properties}/Property[@name='Base']/Link")
        assert BaseLink is not None
        assert Objects[BaseLink.attrib["value"]] == "Sketcher::SketchObject"
        Depth = RootValue.find(f"{Properties}/Property[@name='LengthFwd']/Float")
        assert Depth is not None and float(Depth.attrib["value"]) == Pytest.approx(
            DepthMm
        )
        Engine = RootValue.find(f"{Properties}/Property/ExpressionEngine/Expression")
        assert Engine is not None and Engine.attrib == {
            "path": "LengthFwd",
            "expression": "Parameters.fusion_parameter_242",
        }
        Shape = RootValue.find(f"{Properties}/Property[@name='Shape']/Part")
        assert Shape is not None
        assert [Name for Name in Archive.namelist() if Name.endswith(".Shape.brp")] == [
            Shape.attrib["file"]
        ]
    assert OpenDocument(Output).feature_timeline == Document.feature_timeline


# unresolved source formula references cannot be replaced by a frozen editable depth
def TestFormulaExt(TmpPath: FilePath) -> None:
    Document = OpenDocument(
        KStudyPath / "holdouts-f8c508a73323" / "expression_depth.f3d", strict=False
    )
    Output = TmpPath / "formula.FCStd"
    Result = WriteDocument(Document, Output)
    Transfers = {Value.capability: Value.mode for Value in Result.transfers}
    assert Transfers[Capability.PARAMETRIC_HISTORY] is TransferMode.CARRIER
    assert Transfers[Capability.EXPRESSIONS] is TransferMode.MIXED
    with ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        assert RootValue.find("./Objects/Object[@type='Part::Extrusion']") is None
    StrictOutput = TmpPath / "strict.FCStd"
    with Pytest.raises(AppUsabilityError):
        WriteDocument(Document, StrictOutput, allow_carrier=False)
    assert not StrictOutput.exists()


# direct source transfer must keep one valid solid before and after a live dimension edit
@Pytest.mark.skipif(
    not KOraclePath.is_file(), reason="KIT_FREECAD_ORACLE is unavailable"
)
@Pytest.mark.parametrize(
    ("SampleName", "EditText", "SignValue"),
    (("distance_positive", "25 mm", 1.0), ("distance_negative", "=-25 mm", -1.0)),
)
def TestNativeEdit(
    TmpPath: FilePath, SampleName: str, EditText: str, SignValue: float
) -> None:
    Output = ResolveTemp(TmpPath / "editable.FCStd")
    Saved = ResolveTemp(TmpPath / "edited.FCStd")
    Document = OpenDocument(
        KStudyPath / "extents-f0f33a9a605f" / f"{SampleName}.f3d", strict=False
    )
    _ = WriteDocument(Document, Output)
    RunResult = RunProcess(
        [str(KOraclePath), "-c", f"exec({KEditProbe!r})"],
        env={
            **Environment,
            "KIT_ORACLE_PATH": str(Output),
            "KIT_ORACLE_DEPTH": EditText,
            "KIT_ORACLE_SAVED": str(Saved),
        },
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    Before, After = (
        tuple(map(float, LineValue.split()[1:]))
        for LineValue in RunResult.stdout.splitlines()
        if LineValue.startswith("KIT_FUSION_EDIT ")
    )
    assert Before == Pytest.approx(
        (1700.0 * HalfTurn, 540.0 * HalfTurn, 8.5 * SignValue)
    )
    assert After == Pytest.approx(
        (2500.0 * HalfTurn, 700.0 * HalfTurn, 12.5 * SignValue)
    )
    Readback = OpenDocument(Saved)
    assert Readback.parameters[0].value.value == 2.5 * SignValue
    assert Readback.bodies[0].topology.volume == Pytest.approx(After[0])
