# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import pi as HalfTurn
from pathlib import Path as FilePath
import xml.etree.ElementTree as XmlTree
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.freecad.Adapter import FreeCadAdapterA
from convert.adapters.freecad.ArchiveEditPlan import KEditableBinding
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditExtProfile import GetEditCircle
from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.document.models.DocumentModel import CadDocument

# the native source fixture supplies the original carrier independently of the edit
KSourcePath = (
    FilePath(__file__).parents[3]
    / "re/Fusion/Study/extents-f0f33a9a605f/distance_positive.f3d"
)


# rebuilds let readback tests exercise the archive boundary without requiring a cad executable
def MakeEditShape(DocValue: CadDocument, DistanceMm: float) -> bytes:
    Profile = GetEditCircle(DocValue.feature_timeline[-1], DocValue.sketches[0])
    assert Profile is not None
    Lower, Upper = sorted((0.0, DistanceMm))
    Model, _, _, _ = BuildCircular(
        DocValue.bodies[0].id,
        DocValue.support_planes[0].transform,
        Profile,
        Lower,
        Upper,
        Profile.radius,
        Profile.radius,
    )
    return BrepModelBrep(Model)


# separate sheet and shape replacements reproduce coherent and stale saves against one manifest
def ChangeEditFile(
    Output: FilePath, DistanceMm: float, ShapeData: bytes | None, ChangeMode: str
) -> bytes:
    with ZipFile(Output) as Archive:
        Entries = {
            NameValue: Archive.read(NameValue) for NameValue in Archive.namelist()
        }
    RootValue = XmlTree.fromstring(Entries["Document.xml"])
    Feature = RootValue.find("./Objects/Object[@type='Part::Extrusion']")
    assert Feature is not None
    FeaturePath = f"./ObjectData/Object[@name='{Feature.attrib['name']}']/Properties"
    CellValue = RootValue.find(".//Cell[@alias='fusion_parameter_242']")
    Depth = RootValue.find(f"{FeaturePath}/Property[@name='LengthFwd']/Float")
    Shape = RootValue.find(f"{FeaturePath}/Property[@name='Shape']/Part")
    assert CellValue is not None and Depth is not None and Shape is not None
    CellValue.set("content", f"={DistanceMm:g} mm")
    Depth.set("value", str(DistanceMm))
    if ShapeData is not None:
        Entries[Shape.attrib["file"]] = ShapeData
    if ChangeMode in {"unmarked", "legacy-identity"}:
        Metadata = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties")
        assert Metadata is not None
        Binding = Metadata.find(f"Property[@name='{KEditableBinding}']")
        assert Binding is not None
        Metadata.remove(Binding)
        Metadata.set("Count", str(len(Metadata)))
    if ChangeMode in {"identity", "legacy-identity"}:
        Identity = RootValue.find(f"{FeaturePath}/Property[@name='KitId']/String")
        assert Identity is not None
        Identity.set("value", "removed-binding")
    if ChangeMode in {"carrier-shape", "sketch-shape"}:
        TypeName = (
            "Part::Feature"
            if ChangeMode == "carrier-shape"
            else "Sketcher::SketchObject"
        )
        Other = RootValue.find(f"./Objects/Object[@type='{TypeName}']")
        assert Other is not None
        OtherProps = RootValue.find(
            f"./ObjectData/Object[@name='{Other.attrib['name']}']/Properties"
        )
        assert OtherProps is not None
        OtherShape = OtherProps.find("Property[@name='Shape']")
        if OtherShape is None:
            OtherShape = XmlTree.SubElement(
                OtherProps,
                "Property",
                {"name": "Shape", "type": "Part::PropertyPartShape"},
            )
            OtherProps.set("Count", str(len(OtherProps)))
        OtherPart = OtherShape.find("Part")
        if OtherPart is None:
            OtherPart = XmlTree.SubElement(OtherShape, "Part")
        OtherPart.set("file", Shape.attrib["file"])
    Entries["Document.xml"] = XmlTree.tostring(RootValue, encoding="utf-8")
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        for NameValue, DataValue in Entries.items():
            Archive.writestr(NameValue, DataValue)
    return Buffer.getvalue()


# signed edits must update measures and preserve identities before applying public read filters
@Pytest.mark.parametrize(
    ("DistanceMm", "ChangeMode"),
    ((25.0, "bound"), (-25.0, "unmarked"), (0.021, "bound")),
)
def TestDepthEdit(TmpPath: FilePath, DistanceMm: float, ChangeMode: str) -> None:
    Document = OpenDocument(KSourcePath, strict=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    assert OpenDocument(Output) == Document
    DataValue = ChangeEditFile(
        Output, DistanceMm, MakeEditShape(Document, DistanceMm), ChangeMode
    )
    Readback = OpenDocument(DataValue)
    Parameter = next(
        Value for Value in Readback.parameters if Value.id == "fusion-parameter-242"
    )
    ExpectedValue = (
        (DistanceMm, "mm") if DistanceMm == 0.021 else (DistanceMm / 10.0, "cm")
    )
    assert (Parameter.value.value, Parameter.value.unit) == ExpectedValue
    assert (
        Parameter.expression is not None and Parameter.expression.language == "freecad"
    )
    assert Readback.feature_timeline == Document.feature_timeline
    assert Readback.brep_payloads == Document.brep_payloads
    assert Readback.bodies[0].id == Document.bodies[0].id
    assert Readback.bodies[0].topology.volume == Pytest.approx(
        100.0 * abs(DistanceMm) * HalfTurn
    )
    assert Readback.bodies[0].topology.surface_area == Pytest.approx(
        (200.0 + 20.0 * abs(DistanceMm)) * HalfTurn
    )
    Bounds = Readback.bodies[0].topology.bounding_box
    assert Bounds is not None
    assert (Bounds.minimum.z, Bounds.maximum.z) == tuple(sorted((0.0, DistanceMm)))
    Filtered = OpenDocument(DataValue, include_brep=False)
    assert Filtered.brep is None and Filtered.parameters == Readback.parameters
    Reexport = TmpPath / "reexport.FCStd"
    _ = WriteDocument(Readback, Reexport)
    assert OpenDocument(Reexport) == Readback


# a marked missing feature and a stale attached solid must fail explicitly
@Pytest.mark.parametrize(
    ("ChangeMode", "Reason"),
    (
        ("bound", "shape disagrees"),
        ("identity", "feature is missing"),
        ("legacy-identity", "feature is missing"),
    ),
)
def TestStaleEdit(TmpPath: FilePath, ChangeMode: str, Reason: str) -> None:
    Document = OpenDocument(KSourcePath, strict=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    Stale = ChangeEditFile(Output, 25.0, None, ChangeMode)
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        OpenDocument(Stale)


# a valid edited solid must not hide a second solid on another native object
@Pytest.mark.parametrize(
    ("ChangeMode", "Reason"),
    (
        ("carrier-shape", "additional nonempty shape"),
        ("sketch-shape", "sketch cache disagrees"),
    ),
)
def TestExtraShape(TmpPath: FilePath, ChangeMode: str, Reason: str) -> None:
    Document = OpenDocument(KSourcePath, strict=False)
    Output = TmpPath / "editable.FCStd"
    _ = WriteDocument(Document, Output)
    Edited = ChangeEditFile(Output, 25.0, MakeEditShape(Document, 25.0), ChangeMode)
    with Pytest.raises(FreeCadAdapterA, match=Reason):
        OpenDocument(Edited)
