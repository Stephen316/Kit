# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import pi as HalfTurn, radians as Radians
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from xml.etree.ElementTree import fromstring as ParseXml, tostring as WriteXml
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.EditRev.RevBinding import KRevBinding
from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureAngleRev import AngularRevolve
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the optional target oracle reads and recomputes the actual freecad solid
KOraclePath = GetFreecadPath()


# swapping limits of equal total angle must mirror the solid center through the sketch
KRevProbe = """
import os
import FreeCAD as App

def measures(doc):
    (feature,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
    shape = feature.Shape
    assert feature.Visibility and shape.isValid() and len(shape.Solids) == 1
    print('KIT_REVOLVE', shape.Volume, *shape.Solids[0].CenterOfMass)

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
measures(doc)
doc.recompute()
measures(doc)
sheet = doc.getObject('Parameters')
for alias, value in (('fusion_parameter_258', '25 deg'), ('fusion_parameter_261', '60 deg')):
    sheet.set(sheet.getCellFromAlias(alias), value)
doc.recompute()
measures(doc)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
doc = App.openDocument(os.environ['KIT_ORACLE_SAVED'])
measures(doc)
App.closeDocument(doc.Name)
"""


# the public writer must link native controls to the source sketch and visible solid
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Folder", "SampleName", "AngleDeg", "SideMode"),
    (
        ("models-97a5e41e2ba7", "revolve_full", 360.0, "one_sided"),
        ("models-97a5e41e2ba7", "revolve_partial", 65.0, "one_sided"),
        ("revolvemodes-8eb734486235", "axis_x", 65.0, "one_sided"),
        ("revolvemodes-8eb734486235", "negative", -75.0, "one_sided"),
        ("revolvemodes-8eb734486235", "positive", 65.0, "one_sided"),
        ("revolvemodes-8eb734486235", "symmetric", 130.0, "symmetric"),
        ("revolvemodes-8eb734486235", "two_sided", 85.0, "two_sided"),
    ),
)
def TestNativeRev(
    TmpPath: FilePath, Folder: str, SampleName: str, AngleDeg: float, SideMode: str
) -> None:
    DocValue = OpenDocument(KStudyPath / Folder / f"{SampleName}.f3d", strict=False)
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, AngularRevolve) and Definition.SideMode == SideMode
    Output = TmpPath / f"{SampleName}.FCStd"
    Result = WriteDocument(DocValue, Output)
    Transfers = {Value.capability: Value.mode for Value in Result.transfers}
    assert Result.application_usable and Result.vendor_loadable
    assert Transfers[Capability.BREP] is TransferMode.NATIVE
    assert Transfers[Capability.PARAMETRIC_HISTORY] is TransferMode.MIXED
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
        Binding = RootValue.find(
            f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{KRevBinding}']/String"
        )
        assert Binding is not None and Binding.get("value") == StepValue.id
        Objects = {
            Value.attrib["name"]: Value.attrib["type"]
            for Value in RootValue.findall("./Objects/Object")
        }
        (Revolution,) = (
            NameValue
            for NameValue, TypeValue in Objects.items()
            if TypeValue == "Part::Revolution"
        )
        Props = f"./ObjectData/Object[@name='{Revolution}']/Properties"
        Source = RootValue.find(f"{Props}/Property[@name='Source']/Link")
        assert Source is not None
        assert Objects[Source.attrib["value"]] == "Sketcher::SketchObject"
        SketchProps = (
            f"./ObjectData/Object[@name='{Source.attrib['value']}']/Properties"
        )
        Constraints = RootValue.find(
            f"{SketchProps}/Property[@name='Constraints']/ConstraintList"
        )
        assert Constraints is not None and int(Constraints.attrib["count"]) == 8
        Angle = RootValue.find(f"{Props}/Property[@name='Angle']")
        assert (
            Angle is not None and Angle.attrib["type"] == "App::PropertyFloatConstraint"
        )
        AngleValue = Angle.find("Float")
        assert AngleValue is not None and float(
            AngleValue.attrib["value"]
        ) == Pytest.approx(AngleDeg)
        Symmetric = RootValue.find(f"{Props}/Property[@name='Symmetric']/Bool")
        assert Symmetric is not None
        assert Symmetric.attrib["value"] == str(SideMode != "one_sided").lower()
        Axis = RootValue.find(f"{Props}/Property[@name='Axis']/PropertyVector")
        assert Axis is not None
        Direction = Definition.AxisDirection
        assert tuple(float(Axis.attrib[f"value{Dim}"]) for Dim in "XYZ") == (
            Direction.x,
            Direction.y,
            Direction.z,
        )
        Expressions = {
            Value.attrib["path"]: Value.attrib["expression"]
            for Value in RootValue.findall(
                f"{Props}/Property/ExpressionEngine/Expression"
            )
        }
        Along = Definition.AlongParameterId.replace("-", "_")
        Against = (Definition.AgainstParameterId or "").replace("-", "_")
        if SideMode == "symmetric":
            Cell = RootValue.find(f".//Cell[@alias='{Against}']")
            assert Cell is not None and Cell.attrib["content"] == f"={Along}"
            assert Expressions == {"Angle": f"Parameters.{Along} * 2"}
        elif SideMode == "two_sided":
            assert Expressions["Angle"] == f"Parameters.{Along} + Parameters.{Against}"
            assert (
                f"(Parameters.{Along} - Parameters.{Against}) / 2"
                in Expressions["Placement"]
            )
        else:
            assert Expressions == {"Angle": f"Parameters.{Along}"}
        Shape = RootValue.find(f"{Props}/Property[@name='Shape']/Part")
        assert Shape is not None
        assert [Name for Name in Archive.namelist() if Name.endswith(".Shape.brp")] == [
            Shape.attrib["file"]
        ]
    assert OpenDocument(Output) == DocValue


# unproven sketch axis dependencies keep the exact solid through the carrier path
@KRequiresCodec
def TestRevolveCarrier(TmpPath: FilePath) -> None:
    DocValue = OpenDocument(
        KStudyPath / "revolveaxes-a83b542c4a07" / "sketch_line.f3d", strict=False
    )
    Output = TmpPath / "sketch_line.FCStd"
    Result = WriteDocument(DocValue, Output)
    assert Capability.BREP in Result.native_capabilities
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
        assert not RootValue.findall("./Objects/Object[@type='Part::Revolution']")
        assert any(Name.endswith(".Shape.brp") for Name in Archive.namelist())
    assert OpenDocument(Output) == DocValue


# the reader must reject a cached angle that disagrees with its driving spreadsheet
@KRequiresCodec
def TestStaleRevolve(TmpPath: FilePath) -> None:
    DocValue = OpenDocument(
        KStudyPath / "revolvemodes-8eb734486235" / "positive.f3d", strict=False
    )
    Output = TmpPath / "positive.FCStd"
    _ = WriteDocument(DocValue, Output)
    with ZipFile(Output) as Archive:
        Members = {Name: Archive.read(Name) for Name in Archive.namelist()}
    RootValue = ParseXml(Members["Document.xml"])
    Angle = RootValue.find(
        "./ObjectData/Object/Properties/Property[@name='Angle']/Float"
    )
    assert Angle is not None
    Angle.set("value", "25")
    Members["Document.xml"] = WriteXml(RootValue, encoding="utf-8")
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        for Name, DataValue in Members.items():
            Archive.writestr(Name, DataValue)
    with Pytest.raises(FreeCadAdapterA, match="angle"):
        OpenDocument(Buffer.getvalue())


# a seed in world coordinates must survive loading and recomputing an edited placement
@KRequiresCodec
@Pytest.mark.skipif(
    not KOraclePath.is_file(), reason="KIT_FREECAD_ORACLE is unavailable"
)
def TestAsymmetricNativeEdit(TmpPath: FilePath) -> None:
    Output = ResolveTemp(TmpPath / "two_sided.FCStd")
    Saved = ResolveTemp(TmpPath / "two_sided_edited.FCStd")
    DocValue = OpenDocument(
        KStudyPath / "revolvemodes-8eb734486235" / "two_sided.f3d", strict=False
    )
    _ = WriteDocument(DocValue, Output)
    RunResult = RunProcess(
        [str(KOraclePath), "-c", f"exec({KRevProbe!r})"],
        env={
            **Environment,
            "KIT_ORACLE_PATH": str(Output),
            "KIT_ORACLE_SAVED": str(Saved),
        },
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    Loaded, Rebuilt, Edited, Reopened = (
        tuple(map(float, LineValue.split()[1:]))
        for LineValue in RunResult.stdout.splitlines()
        if LineValue.startswith("KIT_REVOLVE ")
    )
    Volume = 12000.0 * 85.0 * HalfTurn / 180.0
    assert Loaded == Pytest.approx((Volume, 18.82039143727766, 25.0, 5.934046626402039))
    assert Rebuilt == Pytest.approx(Loaded)
    assert Edited == Pytest.approx((*Loaded[:3], -Loaded[3]))
    assert Reopened == Pytest.approx(Edited)
    Readback = OpenDocument(Saved)
    assert Readback.feature_timeline == DocValue.feature_timeline
    assert Readback.sketches == DocValue.sketches
    assert [Value.value.value for Value in Readback.parameters] == Pytest.approx(
        (Radians(25.0), Radians(60.0))
    )
    assert Readback.bodies[0].topology.volume == Pytest.approx(Volume)
    assert Readback.brep != DocValue.brep
    Rewrite = TmpPath / "two_sided_rewrite.FCStd"
    _ = WriteDocument(Readback, Rewrite)
    assert OpenDocument(Rewrite) == Readback
