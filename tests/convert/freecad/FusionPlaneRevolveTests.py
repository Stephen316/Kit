# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from xml.etree.ElementTree import fromstring as ParseXml
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.adapters.freecad.EditPlaneRev.PlaneRevBinding import KPlaneRevBinding
from interchange.enums.EnumDocument import Capability
from interchange.features.FeaturePlaneRev import PlaneRevolve
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# captured controls retain independently authored planes in both extent modes
KSourceFolder = KStudyPath / "revolveto-b1d196f65c46"

# the native oracle independently recomputes both editable plane dependencies
KOraclePath = GetFreecadPath()


# a phase only change detects a stale placement even when volume stays the same
KPlaneProbe = """
import os
import FreeCAD as App

def measures(doc):
    (feature,) = [obj for obj in doc.Objects if obj.TypeId == 'Part::Revolution']
    shape = feature.Shape
    assert feature.Visibility and shape.isValid() and len(shape.Solids) == 1
    assert 'Invalid' not in feature.State and abs(feature.Angle - 80) < 1e-7
    print('KIT_PLANE_REVOLVE', shape.Volume, *shape.Solids[0].CenterOfMass)

doc = App.openDocument(os.environ['KIT_ORACLE_PATH'])
measures(doc)
doc.recompute()
measures(doc)
sheet = doc.getObject('Parameters')
for alias, value in (('fusion_parameter_245', '=32 deg'), ('fusion_parameter_274', '=-48 deg')):
    sheet.set(sheet.getCellFromAlias(alias), value)
doc.recompute()
measures(doc)
doc.saveAs(os.environ['KIT_ORACLE_SAVED'])
App.closeDocument(doc.Name)
doc = App.openDocument(os.environ['KIT_ORACLE_SAVED'])
doc.recompute()
measures(doc)
App.closeDocument(doc.Name)
"""


# every native target has a live placement and links to its original construction step
@KRequiresCodec
@Pytest.mark.parametrize(
    ("SampleName", "AngleDeg"),
    (("negative_plane", 35.0), ("positive_plane", 135.0), ("two_planes", 80.0)),
)
def TestLivePlaneRev(TmpPath: FilePath, SampleName: str, AngleDeg: float) -> None:
    DocValue = OpenDocument(KSourceFolder / f"{SampleName}.f3d", strict=False)
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, PlaneRevolve)
    Output = TmpPath / f"{SampleName}.FCStd"
    Result = WriteDocument(DocValue, Output)
    assert Result.application_usable and Capability.BREP in Result.native_capabilities
    with ZipFile(Output) as Archive:
        Root = ParseXml(Archive.read("Document.xml"))
        Objects = {
            Value.get("name"): Value for Value in Root.findall("./ObjectData/Object")
        }
        (Revolution,) = Root.findall("./Objects/Object[@type='Part::Revolution']")
        NativeName = Revolution.get("name")
        Props = Objects[NativeName]
        Binding = Objects["KitMetadata"].find(
            f"./Properties/Property[@name='{KPlaneRevBinding}']/String"
        )
        assert Binding is not None and Binding.get("value") == StepValue.id
        Angle = Props.find("./Properties/Property[@name='Angle']/Float")
        assert Angle is not None and float(Angle.attrib["value"]) == Pytest.approx(
            AngleDeg
        )
        Expressions = {
            Value.attrib["path"]: Value.attrib["expression"]
            for Value in Props.findall(
                "./Properties/Property/ExpressionEngine/Expression"
            )
        }
        PlaneLinks = [
            Value.attrib["value"]
            for Node in Objects.values()
            for Value in Node.findall(
                "./Properties/Property[@name='ConstructionPlane']/Link"
            )
        ]
        assert len(PlaneLinks) == len(Definition.PlaneSelectionIds)
        for PlaneName in PlaneLinks:
            Placement = Objects[PlaneName].find(
                "./Properties/Property/ExpressionEngine/Expression[@path='Placement']"
            )
            assert (
                Placement is not None
                and "Parameters." in Placement.attrib["expression"]
            )
            assert f"{PlaneName}.Placement.Rotation" in Expressions["Angle"]
            if len(PlaneLinks) == 2:
                assert f"{PlaneName}.Placement.Rotation" in Expressions["Placement"]
        assert [Name for Name in Archive.namelist() if Name.endswith(".Shape.brp")] == [
            f"{NativeName}.Shape.brp"
        ]
    assert OpenDocument(Output) == DocValue


# both construction plane controls move the native angular placement after a save
@KRequiresCodec
@Pytest.mark.skipif(
    not KOraclePath.is_file(), reason="KIT_FREECAD_ORACLE is unavailable"
)
def TestNativePlaneEdit(TmpPath: FilePath) -> None:
    DocValue = OpenDocument(KSourceFolder / "two_planes.f3d", strict=False)
    Output = ResolveTemp(TmpPath / "two_planes.FCStd")
    Saved = ResolveTemp(TmpPath / "two_planes_edited.FCStd")
    _ = WriteDocument(DocValue, Output)
    Result = RunProcess(
        [str(KOraclePath), "-c", f"exec({KPlaneProbe!r})"],
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
        for LineValue in Result.stdout.splitlines()
        if LineValue.startswith("KIT_PLANE_REVOLVE ")
    )
    assert Loaded == Pytest.approx(
        (16755.16081914557, -19.873138799079268, 25.0, 1.7386743535966336)
    )
    assert Rebuilt == Pytest.approx(Loaded)
    assert Edited == Pytest.approx((Loaded[0], -19.754908, 25.0, -2.776371))
    assert Reopened == Pytest.approx(Edited)
