# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import radians as Radians
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from xml.etree.ElementTree import fromstring as ParseXml
from xml.etree.ElementTree import tostring as WriteXml
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.EditAxisRev.AxisRevBinding import KAxisRevBinding
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the independent controls reverse the same construction line endpoints
KAxisFolder = KStudyPath / "revolveaxes-a83b542c4a07"

# the optional native oracle verifies the live construction dependency
KOraclePath = GetFreecadPath()


# changing original native points must move both the guide and the revolved solid
KAxisProbe = """
import os
import FreeCAD as App

def endpoint(axis, index):
    point = axis.Geometry[index]
    return App.Vector(point.X, point.Y, 0)

def measure(doc):
    (feature,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
    shape = feature.Shape
    assert feature.Visibility and 'Invalid' not in feature.State
    assert shape.isValid() and shape.isClosed() and len(shape.Solids) == 1
    print('KIT_AXIS_REVOLVE', shape.Volume, *shape.Solids[0].CenterOfMass)
    return feature

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
measure(doc)
doc.recompute()
rev = measure(doc)
axis, sub = rev.AxisLink
assert sub == ['Edge1'] and axis.getConstruction(3) and not axis.getConstruction(4)
targets = [(11, -9, 0), (25, 27, 0)]
if os.environ['KIT_REVERSED'] == 'yes':
    targets.reverse()
for index, point in enumerate(targets, 1):
    axis.moveGeometry(index, 1, App.Vector(*point), False)
sheet = doc.getObject('Parameters')
sheet.set(sheet.getCellFromAlias('fusion_parameter_311'), '=-41 deg')
doc.recompute()
assert abs(rev.Angle + 41) < 1e-8 and len(axis.Shape.Edges) == 1
measure(doc)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
doc = App.openDocument(os.environ['KIT_ORACLE_SAVED'])
doc.recompute()
rev = measure(doc)
axis = rev.AxisLink[0]
first, second = endpoint(axis, 1), endpoint(axis, 2)
for index, point in ((1, first + App.Vector(3, -1, 0)), (2, first), (1, second)):
    axis.moveGeometry(index, 1, point, False)
doc.recompute()
assert abs(rev.Angle - 41) < 1e-8
measure(doc)
App.closeDocument(doc.Name)

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
doc.recompute()
(rev,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
axis = rev.AxisLink[0]
shift = App.Vector(-8 * (4/5)**0.5, 8 * (1/5)**0.5, 0)
for index in (1, 2):
    axis.moveGeometry(index, 1, endpoint(axis, index) + shift, False)
doc.recompute()
assert abs(rev.Angle - 73) < 1e-8
measure(doc)
doc.saveAs(os.environ['KIT_ORACLE_TOUCH'])
App.closeDocument(doc.Name)
"""


# a hidden linked edge keeps the selected source line as construction geometry
@KRequiresCodec
@Pytest.mark.parametrize("SampleName", ("sketch_line", "sketch_line_reversed"))
def TestAxisRev(TmpPath: FilePath, SampleName: str) -> None:
    DocValue = OpenDocument(KAxisFolder / f"{SampleName}.f3d", strict=False)
    Feature = DocValue.feature_timeline[-1]
    Output = TmpPath / f"{SampleName}.FCStd"
    Result = WriteDocument(DocValue, Output)
    assert Result.application_usable and Capability.BREP in Result.native_capabilities
    with ZipFile(Output) as Archive:
        Root = ParseXml(Archive.read("Document.xml"))
        (Revolution,) = Root.findall("./Objects/Object[@type='Part::Revolution']")
        NameValue = Revolution.get("name")
        Props = Root.find(f"./ObjectData/Object[@name='{NameValue}']/Properties")
        assert Props is not None
        Axis = Props.find("./Property[@name='AxisLink']/LinkSub")
        Source = Props.find("./Property[@name='Source']/Link")
        assert (
            Axis is not None
            and Source is not None
            and Axis[0].attrib == {"value": "Edge1"}
        )
        AxisProps = Root.find(
            f"./ObjectData/Object[@name='{Axis.get('value')}']/Properties"
        )
        assert AxisProps is not None
        Geometry = AxisProps.findall(
            "./Property[@name='Geometry']/GeometryList/Geometry"
        )
        assert len(Geometry) == 5
        assert [
            Node.get("value")
            for Node in AxisProps.findall(
                "./Property[@name='Geometry']/GeometryList/Geometry/Construction"
            )
        ] == ["0", "0", "0", "1", "0"]
        assert (
            len(
                AxisProps.findall(
                    "./Property[@name='Constraints']/ConstraintList/Constrain"
                )
            )
            == 4
        )
        Profile = Root.find(
            f"./ObjectData/Object[@name='{Source.get('value')}']/Properties"
        )
        assert Profile is not None
        assert (
            len(
                Profile.findall(
                    "./Property[@name='Constraints']/ConstraintList/Constrain"
                )
            )
            == 12
        )
        Binding = Root.find(
            f"./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='{KAxisRevBinding}']/String"
        )
        assert Binding is not None and Binding.get("value") == Feature.id
        assert [Name for Name in Archive.namelist() if Name.endswith(".Shape.brp")] == [
            f"{NameValue}.Shape.brp"
        ]
    assert OpenDocument(Output) == DocValue


# a changed solver binding or an invalid result cannot silently return the source snapshot
@KRequiresCodec
@Pytest.mark.parametrize(
    ("PathValue", "Field", "Changed"),
    (
        (".//Property[@name='AxisLink']/LinkSub/Sub", "value", "Edge2"),
        (
            ".//Expression[@path='Angle']",
            "expression",
            "Parameters.fusion_parameter_311",
        ),
        ("./Objects/Object[@type='Part::Revolution']", "Invalid", "1"),
        (".//Constrain[@Name='incidence_4_1']", "SecondPos", "2"),
    ),
)
def TestAxisConflict(
    TmpPath: FilePath, PathValue: str, Field: str, Changed: str
) -> None:
    DocValue = OpenDocument(KAxisFolder / "sketch_line.f3d", strict=False)
    Output = TmpPath / "axis.FCStd"
    _ = WriteDocument(DocValue, Output)
    with ZipFile(Output) as Archive:
        Members = {Name: Archive.read(Name) for Name in Archive.namelist()}
    Root = ParseXml(Members["Document.xml"])
    Target = Root.find(PathValue)
    assert Target is not None
    Target.set(Field, Changed)
    Members["Document.xml"] = WriteXml(Root, encoding="utf-8")
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        for Name, DataValue in Members.items():
            Archive.writestr(Name, DataValue)
    with Pytest.raises(
        FreeCadAdapterA, match="editable sketch axis|constraint identity"
    ):
        OpenDocument(Buffer.getvalue())


# matching actual measures after a signed angle and axis move proves the link survived
@KRequiresCodec
@Pytest.mark.skipif(
    not KOraclePath.is_file(), reason="KIT_FREECAD_ORACLE is unavailable"
)
@Pytest.mark.parametrize("SampleName", ("sketch_line", "sketch_line_reversed"))
def TestAxisNative(TmpPath: FilePath, SampleName: str) -> None:
    DocValue = OpenDocument(KAxisFolder / f"{SampleName}.f3d", strict=False)
    Output = ResolveTemp(TmpPath / "axis.FCStd")
    Saved = ResolveTemp(TmpPath / "axis_edited.FCStd")
    Touch = ResolveTemp(TmpPath / "axis_touch.FCStd")
    _ = WriteDocument(DocValue, Output)
    Result = RunProcess(
        [str(KOraclePath), "-c", f"exec({KAxisProbe!r})"],
        env={
            **Environment,
            "KIT_ORACLE_PATH": str(Output),
            "KIT_ORACLE_SAVED": str(Saved),
            "KIT_ORACLE_TOUCH": str(Touch),
            "KIT_REVERSED": "yes" if SampleName.endswith("reversed") else "no",
        },
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    Loaded, Rebuilt, Edited, Reopened, Swapped, Tangent = (
        tuple(map(float, LineValue.split()[1:]))
        for LineValue in Result.stdout.splitlines()
        if LineValue.startswith("KIT_AXIS_REVOLVE ")
    )
    assert Loaded == Pytest.approx(
        (2446.25347959525, 10.5898463316, 12.0657566092, 6.9116299174)
    )
    assert Rebuilt == Pytest.approx(Loaded)
    assert Edited == Pytest.approx(
        (1221.13212327458, 8.50374594, 12.88153652, -3.83508529)
    )
    assert Reopened == Pytest.approx(Edited)
    assert Swapped == Pytest.approx(Edited)
    assert Tangent == Pytest.approx(
        (815.41782653175, 8.20838627695, 13.25648663652, 2.96212710746)
    )
    Readback = OpenDocument(Saved)
    assert Readback.parameters[0].value.value == Pytest.approx(Radians(-41))
    assert Readback.selections == DocValue.selections
    assert Readback.feature_timeline[:-1] == DocValue.feature_timeline[:-1]
    assert Readback.feature_timeline[-1].id == DocValue.feature_timeline[-1].id
    assert Readback.bodies[0].topology.volume == Pytest.approx(Edited[0])
    Rewrite = TmpPath / "axis_rewrite.FCStd"
    _ = WriteDocument(Readback, Rewrite)
    assert OpenDocument(Rewrite) == Readback
    Contact = OpenDocument(Touch)
    assert Contact.parameters == DocValue.parameters
    assert Contact.bodies[0].topology.volume == Pytest.approx(Tangent[0])
    assert Contact.bodies[0].topology.face_count == 5
