# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from pathlib import Path as FilePath
from xml.etree.ElementTree import fromstring as ParseXml, tostring as XmlBytes
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.ArchiveEditPlan import KEditableBinding, KProfileBinding
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditableExt import FindEditFrame
from convert.adapters.freecad.EditExtRing import GetEditRing
from convert.adapters.freecad.EditExtSolid import BuildEditSolid
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepBody, BrepWire
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.freecad.EditReadTests import ChangeEditFile

# the source rectangle has exact native line incidence and a reciprocal solid creator
KRingSource = (
    FilePath(__file__).parents[3]
    / "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


# signed edits must rebuild the complete prism under the original body and sketch identities
@Pytest.mark.parametrize("DepthMm", (31.5, -18.25))
def TestRingDepth(TmpPath: FilePath, DepthMm: float) -> None:
    Document = OpenDocument(KRingSource, strict=False)
    Feature = Document.feature_timeline[-1]
    PairValue = FindEditFrame(Document, Feature.sketch_id)
    assert PairValue is not None
    Sketch, Plane = PairValue
    Ring = GetEditRing(Feature, Sketch)
    assert Ring is not None
    Output = TmpPath / "ring.FCStd"
    _ = WriteDocument(Document, Output)
    with ZipFile(Output) as Archive:
        RootValue = ParseXml(Archive.read("Document.xml"))
    assert RootValue.find("./Objects/Object[@type='Part::Extrusion']") is not None
    for Property, Expected in (
        (KEditableBinding, Feature.id),
        (KProfileBinding, Sketch.id),
    ):
        Binding = RootValue.find(f".//Property[@name='{Property}']/String")
        assert Binding is not None and Binding.get("value") == Expected
    assert len(RootValue.findall(".//ConstraintList/Constrain")) == 8
    assert OpenDocument(Output) == Document
    Model, Volume, AreaValue, Bounds = BuildEditSolid(
        Document.bodies[0].id, Plane.transform, Ring, DepthMm
    )
    Saved = ChangeEditFile(
        Output, DepthMm, BrepModelBrep(Model), "bound", "fusion_parameter_287"
    )
    Readback = OpenDocument(Saved)
    assert Readback.brep == Model
    assert Readback.sketches == Document.sketches
    assert Readback.feature_timeline == Document.feature_timeline
    assert Readback.brep_payloads == Document.brep_payloads
    Topology = Readback.bodies[0].topology
    assert (Topology.volume, Topology.surface_area, Topology.bounding_box) == (
        Volume,
        AreaValue,
        Bounds,
    )
    assert Volume == 1200 * abs(DepthMm)
    _ = WriteDocument(Readback, Output, overwrite=True)
    assert OpenDocument(Output) == Readback


# a new depth cell alone cannot override a solid that still uses the original depth
def TestStaleRing(TmpPath: FilePath) -> None:
    Document = OpenDocument(KRingSource, strict=False)
    Output = TmpPath / "ring.FCStd"
    _ = WriteDocument(Document, Output)
    Saved = ChangeEditFile(Output, -18.25, None, "bound", "fusion_parameter_287")
    with Pytest.raises(FreeCadAdapterA, match="shape disagrees"):
        OpenDocument(Saved)


# the lower prism cap supplies independent first principles wire evidence for the sketch
def CapWire(Model: BrepModel, Sides: int) -> bytes:
    Wire = BrepWire("wire", Model.loops[0].coedge_ids, closed=True)
    return BrepModelBrep(
        BrepModel(
            vertices=Model.vertices[:Sides],
            curves=Model.curves[:Sides],
            edges=Model.edges[:Sides],
            coedges=Model.coedges[:Sides],
            wires=(Wire,),
            bodies=(BrepBody("body", (), wire_ids=(Wire.id,)),),
        )
    )


# a moved shared vertex must survive readback as the same bound line and point entities
def TestMovedRing(TmpPath: FilePath) -> None:
    Original = OpenDocument(KRingSource, strict=False)
    StepValue = Original.feature_timeline[-1]
    PairValue = FindEditFrame(Original, StepValue.sketch_id)
    assert PairValue is not None
    SketchValue, Plane = PairValue
    Ring = GetEditRing(StepValue, SketchValue)
    assert Ring is not None
    Before, After = PlaneVector(40, 30), PlaneVector(14, 8)
    ChangedRing = tuple(
        LineGeometry(
            After if Value.start == Before else Value.start,
            After if Value.end == Before else Value.end,
        )
        for Value in Ring
    )
    DepthMm = -13.5
    BodyId = Original.bodies[0].id
    Model, Volume, _, _ = BuildEditSolid(BodyId, Plane.transform, ChangedRing, DepthMm)
    CapModel, _, _, _ = BuildEditSolid(BodyId, Plane.transform, ChangedRing, 1.0)
    Output = TmpPath / "ring.FCStd"
    _ = WriteDocument(Original, Output)
    Saved = ChangeEditFile(
        Output, DepthMm, BrepModelBrep(Model), "bound", "fusion_parameter_287"
    )
    with ZipFile(BytesIO(Saved)) as Archive:
        Entries = {Value: Archive.read(Value) for Value in Archive.namelist()}
    RootValue = ParseXml(Entries["Document.xml"])
    Native = RootValue.find("./Objects/Object[@type='Sketcher::SketchObject']")
    assert Native is not None
    NameValue = Native.attrib["name"]
    Props = RootValue.find(f"./ObjectData/Object[@name='{NameValue}']/Properties")
    assert Props is not None
    for TagName, Prefix in (
        ("GeomPoint", ""),
        ("LineSegment", "Start"),
        ("LineSegment", "End"),
    ):
        for NodeValue in Props.findall(f".//Geometry/{TagName}"):
            if (
                float(NodeValue.attrib[Prefix + "X"]),
                float(NodeValue.attrib[Prefix + "Y"]),
            ) == (Before.x, Before.y):
                NodeValue.set(Prefix + "X", str(After.x))
                NodeValue.set(Prefix + "Y", str(After.y))
    Part = Props.find("./Property[@name='Shape']/Part")
    assert Part is not None
    CacheName = f"{NameValue}.Shape.brp"
    Part.set("file", CacheName)
    Entries[CacheName] = CapWire(CapModel, len(Ring))
    Entries["Document.xml"] = XmlBytes(RootValue, encoding="utf-8")
    with ZipFile(Output, "w") as Archive:
        for Entry, Payload in Entries.items():
            Archive.writestr(Entry, Payload)
    Readback = OpenDocument(Output)
    assert GetEditRing(StepValue, Readback.sketches[0]) == ChangedRing
    assert Readback.brep == Model
    assert Readback.bodies[0].topology.volume == Volume == 4995.0
    _ = WriteDocument(Readback, Output, overwrite=True)
    assert OpenDocument(Output) == Readback
