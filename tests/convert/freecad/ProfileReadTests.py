# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import pi as HalfTurn, tau as FullTurn
from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml, tostring as XmlBytes
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditableExt import FindEditFrame
from convert.adapters.freecad.EditExtProfile import GetCenterPoint, GetEditCircle
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepVertex,
    BrepWire,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.freecad.EditReadTests import (
    ChangeEditFile,
    KSourcePath,
    MakeEditShape,
)


# a profile cache can be built independently from the same analytic circle as the solid
def MakeProfileWire(Profile: CircleGeometry, Frame: Transform) -> bytes:
    Center = PlacePrismPoint(Frame, Profile.center, 0.0)
    Seam = PlacePrismPoint(
        Frame, PlaneVector(Profile.center.x + Profile.radius, Profile.center.y), 0.0
    )
    Model = BrepModel(
        curves=(
            CircleCurve("circle", Center, Frame.z_axis, Frame.x_axis, Profile.radius),
        ),
        vertices=(BrepVertex("seam", Seam),),
        edges=(BrepEdge("edge", "seam", "seam", "circle", 0.0, FullTurn),),
        coedges=(BrepCoedge("coedge", "edge"),),
        wires=(BrepWire("wire", ("coedge",), closed=True),),
        bodies=(BrepBody("body", (), wire_ids=("wire",)),),
    )
    return BrepModelBrep(Model)


# coherent and stale archive evidence share the same original sketch and depth identities
def WriteProfile(
    Original: CadDocument,
    Export: FilePath,
    Target: FilePath,
    Profile: CircleGeometry,
    DepthMm: float,
    Stale: str,
) -> None:
    StepValue = Original.feature_timeline[-1]
    FramePair = FindEditFrame(Original, StepValue.sketch_id)
    assert FramePair is not None
    SketchValue, Plane = FramePair
    OldCircle = GetEditCircle(StepValue, SketchValue)
    OldCenter = GetCenterPoint(SketchValue)
    assert OldCircle is not None and OldCenter is not None
    SolidProfile = OldCircle if Stale == "solid" else Profile
    WireProfile = OldCircle if Stale == "wire" else Profile
    Changed = ChangeEditFile(
        Export, DepthMm, MakeEditShape(Original, DepthMm, SolidProfile), "bound"
    )
    with ZipFile(BytesIO(Changed)) as Archive:
        Entries = {Value: Archive.read(Value) for Value in Archive.namelist()}
    RootValue = ParseXml(Entries["Document.xml"])
    NativeSketch = RootValue.find("./Objects/Object[@type='Sketcher::SketchObject']")
    assert NativeSketch is not None
    NameValue = NativeSketch.attrib["name"]
    Props = RootValue.find(f"./ObjectData/Object[@name='{NameValue}']/Properties")
    assert Props is not None
    Geometries = Props.find("./Property[@name='Geometry']/GeometryList")
    assert Geometries is not None
    Circle = Geometries.find("./Geometry/Circle")
    Center = Geometries[SketchValue.entities.index(OldCenter)].find("./GeomPoint")
    assert Circle is not None and Center is not None
    Circle.attrib.update(
        CenterX=str(Profile.center.x),
        CenterY=str(Profile.center.y),
        Radius=str(Profile.radius),
    )
    Center.attrib.update(X=str(Profile.center.x), Y=str(Profile.center.y))
    if Stale != "missing":
        Part = Props.find("./Property[@name='Shape']/Part")
        assert Part is not None
        CacheName = f"{NameValue}.Shape.brp"
        Part.set("file", CacheName)
        Entries[CacheName] = MakeProfileWire(WireProfile, Plane.transform)
    Entries["Document.xml"] = XmlBytes(RootValue, encoding="utf-8")
    with ZipFile(Target, "w") as Archive:
        for Entry, Payload in Entries.items():
            Archive.writestr(Entry, Payload)


# profile edits rebuild the solid and leave a profile only depth control untouched
@Pytest.mark.parametrize("DepthMm", (17.0, -23.0))
def TestProfileEdit(TmpPath: FilePath, DepthMm: float) -> None:
    Original = OpenDocument(KSourcePath, strict=False)
    Export, Target = TmpPath / "export.FCStd", TmpPath / "saved.FCStd"
    _ = WriteDocument(Original, Export)
    Profile = CircleGeometry(PlaneVector(3.5, -6.25), 11.5)
    WriteProfile(Original, Export, Target, Profile, DepthMm, "")
    Readback = OpenDocument(Target)
    assert GetEditCircle(Readback.feature_timeline[-1], Readback.sketches[0]) == Profile
    assert Readback.feature_timeline == Original.feature_timeline
    assert Readback.brep_payloads == Original.brep_payloads
    assert Readback.bodies[0].id == Original.bodies[0].id
    assert Readback.bodies[0].topology.volume == Pytest.approx(
        HalfTurn * 11.5**2 * abs(DepthMm)
    )
    if DepthMm == 17.0:
        assert Readback.parameters == Original.parameters
    _ = WriteDocument(Readback, Export, overwrite=True)
    assert OpenDocument(Export) == Readback


# each independently saved shape must describe the same radius and center as the sketch
@Pytest.mark.parametrize(
    ("Stale", "Reason"),
    (
        ("wire", "sketch cache disagrees"),
        ("solid", "shape disagrees"),
        ("missing", "no saved sketch shape"),
    ),
)
def TestProfileProof(TmpPath: FilePath, Stale: str, Reason: str) -> None:
    Original = OpenDocument(KSourcePath, strict=False)
    Export, Target = TmpPath / "export.FCStd", TmpPath / "saved.FCStd"
    _ = WriteDocument(Original, Export)
    WriteProfile(
        Original,
        Export,
        Target,
        CircleGeometry(PlaneVector(3.5, -6.25), 11.5),
        17.0,
        Stale,
    )
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        OpenDocument(Target)
